# -*- coding: utf-8 -*-
"""Cliente LLM (Gemini / Groq) con errores tipados, listado de modelos y prueba de conexión."""
import json
import logging
import socket
import time
import urllib.error
import urllib.parse
import urllib.request

_logger = logging.getLogger(__name__)

PARAM_PREFIX = "chatbot_assistant"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
DEFAULT_TIMEOUT = 45
MAX_RETRIES = 2  # reintentos adicionales ante timeout / cuota / 5xx
RETRY_BASE_DELAY_SEC = 1.5

# Mensajes para el chat (tono humano, sin jerga técnica).
USER_MESSAGES = {
    "inactive": (
        "El asistente está desactivado por ahora. "
        "Pide al administrador que lo active en Ajustes."
    ),
    "missing_key": (
        "Todavía no puedo responder: falta configurar el servicio de IA. "
        "Avísale al administrador."
    ),
    "timeout": (
        "Ahora mismo no pude responder a tiempo. "
        "¿Puedes intentar de nuevo en un momento?"
    ),
    "network": (
        "No pude conectarme al servicio de IA. "
        "Revisa tu conexión e intenta de nuevo."
    ),
    "rate_limit": (
        "Hay mucha demanda en este momento. "
        "Espera un minuto e intenta otra vez."
    ),
    "auth": (
        "Hay un problema con la configuración del asistente. "
        "Avísale al administrador."
    ),
    "model": (
        "Hay un problema con el modelo de IA configurado. "
        "Avísale al administrador."
    ),
    "server": (
        "El servicio de IA no está disponible por ahora. "
        "Intenta de nuevo un poco más tarde."
    ),
    "invalid_json": (
        "No logré interpretar bien tu consulta. "
        "¿Puedes formularla de otra forma?"
    ),
    "blocked": (
        "No pude procesar esa consulta. "
        "Prueba reformularla con otras palabras."
    ),
    "bad_response": (
        "Recibí una respuesta inesperada del servicio de IA. "
        "Intenta de nuevo en un momento."
    ),
    "generic": (
        "No pude responder tu mensaje ahora. "
        "Intenta de nuevo en un momento."
    ),
}

# Mensajes para Ajustes / diagnóstico (más concretos).
ADMIN_MESSAGES = {
    "inactive": "El asistente está desactivado en Ajustes → Chatbot.",
    "missing_key": "Indique la API Key antes de continuar.",
    "timeout": "Timeout: el proveedor de IA no respondió a tiempo.",
    "network": "No se pudo conectar con el proveedor LLM (red).",
    "rate_limit": "Cuota/límite alcanzado (HTTP 429). Espere o cambie de modelo.",
    "auth": "API Key inválida o sin permiso (401/403).",
    "model": "Modelo no encontrado o no disponible (404).",
    "server": "Error del proveedor de IA (5xx). Reintente más tarde.",
    "invalid_json": "El modelo no devolvió un JSON válido.",
    "blocked": "El proveedor rechazó la solicitud (promptFeedback).",
    "bad_response": "Respuesta inesperada del proveedor LLM.",
    "generic": "Error al llamar al proveedor LLM.",
    "missing_model": "Indique el modelo antes de probar la conexión.",
    "model_not_found": (
        "El modelo indicado no aparece en la lista del proveedor. "
        "Use 'Listar modelos' y elija uno Flash disponible."
    ),
}


class LLMClientError(Exception):
    """Error controlado del proveedor LLM."""

    def __init__(self, code, message=None, admin_message=None):
        self.code = code
        key = code if isinstance(code, str) else None
        self.message = message or USER_MESSAGES.get(key) or USER_MESSAGES["generic"]
        self.admin_message = (
            admin_message
            or ADMIN_MESSAGES.get(key)
            or (message if message else ADMIN_MESSAGES["generic"])
        )
        super().__init__(self.message)


def _user_error(message):
    try:
        from odoo.exceptions import UserError
        return UserError(message)
    except ImportError:
        return RuntimeError(message)


def _is_retryable(exc):
    code = getattr(exc, "code", None)
    if code in ("timeout", "rate_limit", "server", "network"):
        return True
    if isinstance(code, int) and (code == 429 or code >= 500):
        return True
    return False


def get_chatbot_config(env):
    """Lee la configuración del chatbot desde ir.config_parameter (Ajustes)."""
    icp = env["ir.config_parameter"].sudo()
    active = icp.get_param(f"{PARAM_PREFIX}.active", "True")
    provider = icp.get_param(f"{PARAM_PREFIX}.provider", "gemini") or "gemini"
    default_model = DEFAULT_GEMINI_MODEL if provider == "gemini" else DEFAULT_GROQ_MODEL
    return {
        "active": str(active).lower() in ("1", "true", "yes"),
        "provider": provider,
        "api_key": icp.get_param(f"{PARAM_PREFIX}.api_key", "") or "",
        "model": icp.get_param(f"{PARAM_PREFIX}.model", default_model) or default_model,
        "temperature": float(icp.get_param(f"{PARAM_PREFIX}.temperature", "0.1") or 0.1),
        "timeout": int(
            icp.get_param(f"{PARAM_PREFIX}.timeout", str(DEFAULT_TIMEOUT)) or DEFAULT_TIMEOUT
        ),
    }


def complete_json(env, system_prompt, user_message):
    """Llama al LLM configurado y espera una respuesta JSON (con reintentos)."""
    config = get_chatbot_config(env)
    if not config["active"]:
        raise _user_error(USER_MESSAGES["inactive"])
    if not config["api_key"]:
        raise _user_error(USER_MESSAGES["missing_key"])

    provider = (config["provider"] or "gemini").lower()
    last_exc = None
    attempts = 1 + MAX_RETRIES
    for attempt in range(attempts):
        try:
            if provider == "groq":
                raw = _call_groq(config, system_prompt, user_message)
            else:
                raw = _call_gemini(config, system_prompt, user_message)
            return _parse_json_response(raw)
        except LLMClientError as exc:
            last_exc = exc
            if not _is_retryable(exc) or attempt >= attempts - 1:
                _logger.warning(
                    "LLM falló (code=%s attempt=%s/%s): %s",
                    exc.code, attempt + 1, attempts, exc.admin_message,
                )
                raise _user_error(exc.message) from exc
            delay = RETRY_BASE_DELAY_SEC * (2 ** attempt)
            _logger.warning(
                "LLM reintento %s/%s en %.1fs (code=%s): %s",
                attempt + 1, attempts, delay, exc.code, exc.admin_message,
            )
            time.sleep(delay)

    raise _user_error(last_exc.message if last_exc else USER_MESSAGES["generic"])


def test_connection(config):
    """
    Valida API key + modelo con una petición mínima.
    Retorna dict: ok, provider, model, latency_ms, message, models (opcional).
    """
    started = time.perf_counter()
    provider = (config.get("provider") or "gemini").lower()
    api_key = (config.get("api_key") or "").strip()
    model = (config.get("model") or "").strip()
    timeout = int(config.get("timeout") or DEFAULT_TIMEOUT)

    if not api_key:
        raise LLMClientError("missing_key")
    if not model:
        raise LLMClientError("missing_model", admin_message=ADMIN_MESSAGES["missing_model"])

    try:
        if provider == "groq":
            models = list_groq_models(api_key, timeout)
            _call_groq(
                {
                    "api_key": api_key,
                    "model": model,
                    "temperature": 0.0,
                    "timeout": timeout,
                },
                'Responde solo con JSON: {"ok": true}',
                "ping",
            )
        else:
            models = list_gemini_models(api_key, timeout)
            ids_plain = {m["id"].replace("models/", "") for m in models}
            if model.replace("models/", "") not in ids_plain:
                raise LLMClientError(
                    "model_not_found",
                    admin_message=ADMIN_MESSAGES["model_not_found"],
                )
            _call_gemini(
                {
                    "api_key": api_key,
                    "model": model.replace("models/", ""),
                    "temperature": 0.0,
                    "timeout": timeout,
                },
                'Responde solo con JSON: {"ok": true}',
                "ping",
            )
    except LLMClientError:
        raise
    except Exception as exc:
        _logger.exception("test_connection unexpected")
        raise LLMClientError(
            "generic",
            admin_message="Error inesperado al probar la conexión: %s" % exc,
        ) from exc

    latency_ms = int((time.perf_counter() - started) * 1000)
    provider_label = "Groq" if provider == "groq" else "Google Gemini"
    return {
        "ok": True,
        "provider": provider_label,
        "model": model.replace("models/", ""),
        "latency_ms": latency_ms,
        "message": "Conexión exitosa",
        "models": models,
    }


def list_models(config):
    """Lista modelos disponibles según proveedor."""
    provider = (config.get("provider") or "gemini").lower()
    api_key = (config.get("api_key") or "").strip()
    timeout = int(config.get("timeout") or DEFAULT_TIMEOUT)
    if not api_key:
        raise LLMClientError("missing_key")
    if provider == "groq":
        return list_groq_models(api_key, timeout)
    return list_gemini_models(api_key, timeout)


def list_gemini_models(api_key, timeout=None):
    timeout = DEFAULT_TIMEOUT if timeout is None else timeout
    url = "https://generativelanguage.googleapis.com/v1beta/models?key=%s&pageSize=100" % (
        urllib.parse.quote(api_key)
    )
    data = _http_json_get(url, timeout)
    result = []
    for item in data.get("models") or []:
        methods = item.get("supportedGenerationMethods") or []
        if "generateContent" not in methods:
            continue
        name = (item.get("name") or "").replace("models/", "")
        if not name:
            continue
        result.append({
            "id": name,
            "display_name": item.get("displayName") or name,
            "description": (item.get("description") or "")[:200],
        })
    result.sort(key=lambda m: (0 if "flash" in m["id"].lower() else 1, m["id"]))
    return result


def list_groq_models(api_key, timeout=None):
    timeout = DEFAULT_TIMEOUT if timeout is None else timeout
    url = "https://api.groq.com/openai/v1/models"
    headers = {"Authorization": "Bearer %s" % api_key}
    data = _http_json_get(url, timeout, headers=headers)
    result = []
    for item in data.get("data") or []:
        mid = item.get("id") or ""
        if not mid:
            continue
        result.append({
            "id": mid,
            "display_name": mid,
            "description": "",
        })
    result.sort(key=lambda m: m["id"])
    return result


def suggest_default_model(models, provider="gemini"):
    ids = [m["id"] for m in models]
    if provider == "groq":
        for preferred in (DEFAULT_GROQ_MODEL, "llama-3.1-70b-versatile", "llama-3.1-8b-instant"):
            if preferred in ids:
                return preferred
        return ids[0] if ids else DEFAULT_GROQ_MODEL
    for preferred in (
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-flash-latest",
    ):
        if preferred in ids:
            return preferred
    for mid in ids:
        if "flash" in mid.lower() and "image" not in mid.lower() and "tts" not in mid.lower():
            return mid
    return ids[0] if ids else DEFAULT_GEMINI_MODEL


def _parse_json_response(raw_text):
    text = (raw_text or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                data = json.loads(text[start : end + 1])
            except json.JSONDecodeError as exc:
                _logger.warning("LLM JSON inválido: %s", text[:500])
                raise LLMClientError("invalid_json") from exc
        else:
            _logger.warning("LLM respuesta no JSON: %s", text[:500])
            raise LLMClientError("invalid_json")

    if not isinstance(data, dict):
        raise LLMClientError("invalid_json")
    return data


def _map_http_error(code, err_body=""):
    body_l = (err_body or "").lower()
    if code == 401 or code == 403 or "api key not valid" in body_l or "invalid api key" in body_l:
        return LLMClientError("auth")
    if code == 404:
        return LLMClientError("model")
    if code == 429:
        return LLMClientError("rate_limit")
    if code >= 500:
        return LLMClientError("server")
    return LLMClientError(
        "generic",
        admin_message="Error al llamar al proveedor LLM (HTTP %s)." % code,
    )


def _http_json_get(url, timeout, headers=None):
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except socket.timeout as exc:
        raise LLMClientError("timeout") from exc
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        _logger.error("LLM HTTP GET %s: %s", exc.code, err_body[:800])
        raise _map_http_error(exc.code, err_body) from exc
    except urllib.error.URLError as exc:
        reason = str(getattr(exc, "reason", exc))
        if "timed out" in reason.lower():
            raise LLMClientError("timeout") from exc
        _logger.error("LLM red GET: %s", exc)
        raise LLMClientError("network") from exc


def _http_json(url, payload, headers, timeout):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except socket.timeout as exc:
        raise LLMClientError("timeout") from exc
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        _logger.error("LLM HTTP %s: %s", exc.code, err_body[:800])
        raise _map_http_error(exc.code, err_body) from exc
    except urllib.error.URLError as exc:
        reason = str(getattr(exc, "reason", exc))
        if "timed out" in reason.lower():
            raise LLMClientError("timeout") from exc
        _logger.error("LLM red: %s", exc)
        raise LLMClientError("network") from exc


def _call_gemini(config, system_prompt, user_message):
    model = (config.get("model") or DEFAULT_GEMINI_MODEL).replace("models/", "")
    api_key = config["api_key"]
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "%s:generateContent?key=%s" % (urllib.parse.quote(model), urllib.parse.quote(api_key))
    )
    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_message}]}],
        "generationConfig": {
            "temperature": config["temperature"],
            "responseMimeType": "application/json",
        },
    }
    headers = {"Content-Type": "application/json"}
    data = _http_json(url, payload, headers, config["timeout"])
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        _logger.error("Respuesta Gemini inesperada: %s", data)
        if isinstance(data, dict) and data.get("promptFeedback"):
            raise LLMClientError("blocked") from exc
        raise LLMClientError("bad_response") from exc


def _call_groq(config, system_prompt, user_message):
    model = config.get("model") or DEFAULT_GROQ_MODEL
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": model,
        "temperature": config["temperature"],
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer %s" % config["api_key"],
    }
    data = _http_json(url, payload, headers, config["timeout"])
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        _logger.error("Respuesta Groq inesperada: %s", data)
        raise LLMClientError("bad_response") from exc
