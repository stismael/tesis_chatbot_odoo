# -*- coding: utf-8 -*-
"""Unit-style checks for validator/prompt (no Odoo required)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "addons" / "custom" / "chatbot_assistant"))

from services.validator import validate_llm_output, merge_pending_entities  # noqa: E402


def test_ready_factura():
    data = {
        "intent": "consultar_factura",
        "entities": {"invoice_number": "INV/2026/00001"},
        "status": "ready",
        "missing_entities": [],
    }
    v = validate_llm_output(data)
    assert v["ok"] and v["status"] == "ready"
    assert v["entities"]["invoice_number"] == "INV/2026/00001"


def test_missing_stock():
    data = {
        "intent": "consultar_stock",
        "entities": {},
        "status": "ready",
        "missing_entities": [],
    }
    v = validate_llm_output(data)
    assert v["status"] == "missing_information"


def test_reject_unknown_intent():
    data = {"intent": "borrar_todo", "entities": {}, "status": "ready"}
    v = validate_llm_output(data)
    assert v["intent"] == "fuera_de_alcance"
    assert v["status"] == "rejected"


def test_merge_pending():
    pending = {"customer_name": "Comercial Andina S.A.", "invoice_number": None}
    new = {"invoice_number": "INV/2026/00001", "customer_name": None}
    merged = merge_pending_entities(pending, new)
    assert merged["customer_name"] == "Comercial Andina S.A."
    assert merged["invoice_number"] == "INV/2026/00001"


def test_stock_facturacion_requires_product():
    data = {
        "intent": "consultar_stock_facturacion_producto",
        "entities": {"date_from": "2026-07-01", "date_to": "2026-07-31"},
        "status": "ready",
    }
    v = validate_llm_output(data)
    assert v["status"] == "missing_information"
    assert "product_name" in v["missing_entities"]

    data["entities"]["product_code"] = "FIL-M01"
    v = validate_llm_output(data)
    assert v["status"] == "ready"
    assert v["entities"]["product_code"] == "FIL-M01"


def test_dates_normalized():
    data = {
        "intent": "consultar_stock_facturacion_producto",
        "entities": {"product_code": "FIL-M01", "date_from": "2026-07-01T00:00:00", "date_to": "julio"},
        "status": "ready",
    }
    v = validate_llm_output(data)
    assert v["entities"]["date_from"] == "2026-07-01"
    assert v["entities"]["date_to"] is None


def test_prompt_includes_today():
    from services.prompt_builder import ALLOWED_INTENTS, build_user_payload
    assert "consultar_stock_facturacion_producto" in ALLOWED_INTENTS
    assert "Fecha actual: 2026-07-15" in build_user_payload("stock FIL-M01", today="2026-07-15")


def test_dataset_loads():
    path = ROOT / "data" / "eval" / "eval_dataset.jsonl"
    n = 0
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                json.loads(line)
                n += 1
    assert n >= 50, n


def test_http_error_mapping():
    from services.llm_client import _map_http_error
    assert _map_http_error(401).code == "auth"
    assert _map_http_error(403).code == "auth"
    assert _map_http_error(404).code == "model"
    assert _map_http_error(429).code == "rate_limit"
    assert _map_http_error(500).code == "server"
    # El mensaje al usuario no expone códigos HTTP; el del administrador sí da el detalle.
    assert "401" not in _map_http_error(401).message
    assert "401" in _map_http_error(401).admin_message
    assert "429" in _map_http_error(429).admin_message


def test_gemini_key_not_in_url():
    from services import llm_client
    calls = []

    def fake_http(url, payload, headers, timeout):
        calls.append((url, headers))
        return {"candidates": [{"content": {"parts": [{"text": "{}"}]}}]}

    original = llm_client._http_json
    llm_client._http_json = fake_http
    try:
        llm_client._call_gemini(
            {"api_key": "CLAVE-SECRETA", "model": "gemini-2.5-flash", "temperature": 0.1, "timeout": 5},
            "sistema", "usuario",
        )
    finally:
        llm_client._http_json = original
    url, headers = calls[0]
    assert "CLAVE-SECRETA" not in url
    assert headers["x-goog-api-key"] == "CLAVE-SECRETA"


def test_token_usage_parsing():
    from services.llm_client import _gemini_usage, _groq_usage
    gemini = {"usageMetadata": {"promptTokenCount": 1500, "candidatesTokenCount": 90, "thoughtsTokenCount": 400}}
    assert _gemini_usage(gemini) == {"tokens_prompt": 1500, "tokens_output": 90, "tokens_thinking": 400}
    groq = {"usage": {"prompt_tokens": 1400, "completion_tokens": 70}}
    assert _groq_usage(groq) == {"tokens_prompt": 1400, "tokens_output": 70, "tokens_thinking": 0}
    assert _gemini_usage({}) == {"tokens_prompt": 0, "tokens_output": 0, "tokens_thinking": 0}


def test_llm_error_keeps_code():
    from services.llm_client import ChatbotLLMError, _user_error
    err = _user_error("mensaje", "timeout")
    assert isinstance(err, ChatbotLLMError) and err.code == "timeout" and err.args[0] == "mensaje"


def _capture_gemini_payload(model):
    from services import llm_client
    from services.prompt_builder import RESPONSE_SCHEMA
    payloads = []

    def fake_http(url, payload, headers, timeout):
        payloads.append(payload)
        return {"candidates": [{"content": {"parts": [{"text": "{}"}]}}]}

    original = llm_client._http_json
    llm_client._http_json = fake_http
    try:
        llm_client._call_gemini(
            {"api_key": "k", "model": model, "temperature": 0.1, "timeout": 5},
            "sistema", "usuario", response_schema=RESPONSE_SCHEMA,
        )
    finally:
        llm_client._http_json = original
    return payloads[0]["generationConfig"]


def test_gemini_flash_sin_pensamiento_y_con_esquema():
    from services.prompt_builder import RESPONSE_SCHEMA
    config = _capture_gemini_payload("gemini-2.5-flash")
    assert config["thinkingConfig"] == {"thinkingBudget": 0}
    assert config["responseSchema"] is RESPONSE_SCHEMA
    assert config["responseMimeType"] == "application/json"
    assert _capture_gemini_payload("gemini-2.5-flash-lite")["thinkingConfig"] == {"thinkingBudget": 0}
    # 2.5 Pro no permite apagar el razonamiento: se deja la configuración del proveedor.
    assert "thinkingConfig" not in _capture_gemini_payload("gemini-2.5-pro")


def test_esquema_coincide_con_el_validador():
    from services.prompt_builder import ALLOWED_INTENTS, ENTITY_KEYS, RESPONSE_SCHEMA
    from services.validator import ALLOWED_STATUS
    props = RESPONSE_SCHEMA["properties"]
    assert props["intent"]["enum"] == list(ALLOWED_INTENTS)
    assert set(props["entities"]["properties"]) == set(ENTITY_KEYS)
    assert set(props["status"]["enum"]) <= ALLOWED_STATUS


class _FakeICP:
    def __init__(self, params):
        self.params = params

    def sudo(self):
        return self

    def get_param(self, key, default=None):
        return self.params.get(key, default)


def test_un_solo_reintento():
    from services import llm_client
    env = {"ir.config_parameter": _FakeICP({"chatbot_assistant.api_key": "k"})}
    calls = []

    def fake_http(url, payload, headers, timeout):
        calls.append(timeout)
        raise llm_client.LLMClientError("timeout")

    original_http, original_sleep = llm_client._http_json, llm_client.time.sleep
    llm_client._http_json = fake_http
    llm_client.time.sleep = lambda _s: None
    meta = {}
    try:
        llm_client.complete_json(env, "sistema", "usuario", meta=meta)
        raise AssertionError("debía fallar")
    except llm_client.ChatbotLLMError as exc:
        assert exc.code == "timeout"
    finally:
        llm_client._http_json, llm_client.time.sleep = original_http, original_sleep
    assert calls == [20, 20], calls
    assert meta["retries"] == 1


def _with_fake_get(pages, func, *args):
    from services import llm_client
    urls = []

    def fake_get(url, timeout, headers=None):
        urls.append(url)
        return pages[len(urls) - 1]

    original = llm_client._http_json_get
    llm_client._http_json_get = fake_get
    try:
        return func(*args), urls
    finally:
        llm_client._http_json_get = original


def test_gemini_lista_todas_las_paginas_y_solo_texto():
    from services.llm_client import list_gemini_models
    gen = ["generateContent"]
    pages = [
        {"models": [
            {"name": "models/gemini-2.5-flash", "supportedGenerationMethods": gen, "inputTokenLimit": 1048576},
            {"name": "models/gemini-2.5-flash-image", "supportedGenerationMethods": gen},
            {"name": "models/text-embedding-004", "supportedGenerationMethods": ["embedContent"]},
        ], "nextPageToken": "PAG2"},
        {"models": [
            {"name": "models/gemini-2.5-pro", "supportedGenerationMethods": gen},
            {"name": "models/gemini-2.5-flash-preview-tts", "supportedGenerationMethods": gen},
        ]},
    ]
    models, urls = _with_fake_get(pages, list_gemini_models, "k")
    assert [m["id"] for m in models] == ["gemini-2.5-flash", "gemini-2.5-pro"], models
    assert models[0]["input_token_limit"] == 1048576
    assert len(urls) == 2 and "pageToken=PAG2" in urls[1]


def test_groq_solo_modelos_de_texto_activos():
    from services.llm_client import list_groq_models
    pages = [{"data": [
        {"id": "llama-3.3-70b-versatile", "active": True, "context_window": 131072, "owned_by": "Meta"},
        {"id": "whisper-large-v3", "active": True},
        {"id": "meta-llama/llama-guard-4-12b", "active": True},
        {"id": "playai-tts", "active": True},
        {"id": "modelo-retirado", "active": False},
        {"id": "qwen/qwen3-32b", "active": True},
    ]}]
    models, _urls = _with_fake_get(pages, list_groq_models, "k")
    assert [m["id"] for m in models] == ["llama-3.3-70b-versatile", "qwen/qwen3-32b"], models
    assert models[0]["input_token_limit"] == 131072


if __name__ == "__main__":
    test_ready_factura()
    test_missing_stock()
    test_reject_unknown_intent()
    test_merge_pending()
    test_stock_facturacion_requires_product()
    test_dates_normalized()
    test_prompt_includes_today()
    test_dataset_loads()
    test_http_error_mapping()
    test_gemini_key_not_in_url()
    test_token_usage_parsing()
    test_llm_error_keeps_code()
    test_gemini_flash_sin_pensamiento_y_con_esquema()
    test_esquema_coincide_con_el_validador()
    test_un_solo_reintento()
    test_gemini_lista_todas_las_paginas_y_solo_texto()
    test_groq_solo_modelos_de_texto_activos()
    print("OK: validator + dataset + LLM error mapping checks passed")
