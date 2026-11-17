# -*- coding: utf-8 -*-
"""
Evaluación del chatbot con la IA real (Capítulo 5).

Envía cada consulta del dataset al asistente, como si la escribiera un usuario, y compara:
- la intención y las entidades que interpretó la IA,
- el comportamiento (ejecutar, aclarar, rechazar, conversar),
- y, en las consultas que deben ejecutarse, los datos devueltos contra una referencia
  independiente calculada directamente en Odoo (scripts/eval_reference.py), no contra el texto.

Uso desde el host (PowerShell): .\\scripts\\run-chatbot-eval.ps1
Requiere la API key configurada en Ajustes → Chatbot asistente.
"""
import importlib.util
import json
import re
import statistics
import time
from datetime import date
from pathlib import Path

DATA_INTENTS = (
    "consultar_factura", "consultar_stock", "consultar_ventas_cliente",
    "consultar_vendedor_cliente", "consultar_stock_facturacion_producto",
)
PROVIDER_FAILURE = "llm_unavailable"


def _load_reference():
    """Carga eval_reference.py desde la misma carpeta (o /tmp dentro del contenedor)."""
    here = Path(globals().get("__file__") or "/tmp/chatbot_eval_runner.py").parent
    for candidate in (here / "eval_reference.py", Path("/tmp/eval_reference.py")):
        if candidate.exists():
            spec = importlib.util.spec_from_file_location("eval_reference", candidate)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    raise FileNotFoundError("No se encontró eval_reference.py")


def contains_text(reply, text):
    """
    Busca un texto esperado sin aceptar su negación: «pagada» no coincide con «no pagada» (antes se
    contaba como acierto). Las palabras pueden ser el inicio de otra («factur» → «facturado»); los
    números y códigos deben aparecer completos («1250» no coincide con «12500»).
    """
    reply = (reply or "").lower()
    text = text.lower()
    end = "" if text.isalpha() else r"(?![0-9])"
    pattern = r"(?<![\w])(?<!no )" + re.escape(text) + end
    return re.search(pattern, reply) is not None


def entities_match(expected, actual):
    """Las entidades esperadas deben estar en lo que extrajo la IA (sin distinguir mayúsculas)."""
    if not expected:
        return None  # la consulta no evalúa entidades
    actual = actual or {}
    for key, value in expected.items():
        if value is None:
            continue
        got = actual.get(key)
        if got is None:
            return False
        want_s, got_s = str(value).strip().casefold(), str(got).strip().casefold()
        if want_s not in got_s and got_s not in want_s:
            return False
    return True


def behavior_ok(item, result):
    """¿El asistente hizo lo que se esperaba? Una sola respuesta correcta por consulta."""
    behavior = item["expected_behavior"]
    intent = result.get("intent")
    outcome = result.get("outcome")
    status = result.get("status")
    if behavior == "execute":
        return outcome == "answered"
    if behavior == "clarify":
        return outcome == "clarification" and status in ("missing_information", "ambiguous")
    if behavior == "reject":
        return outcome == "rejected"
    if behavior == "converse":
        reply = result.get("reply") or ""
        return outcome == "conversation" and bool(reply) and not any(ch.isdigit() for ch in reply)
    if behavior == "not_conversation":
        # Pregunta de datos escrita como charla: debe ir por la intención de datos esperada.
        return intent == item.get("expected_intent") and intent in DATA_INTENTS
    raise ValueError("Comportamiento esperado desconocido en %s: %s" % (item["id"], behavior))


def _percentile(values, pct):
    if not values:
        return 0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round(pct / 100 * len(ordered) + 0.5) - 1))
    return ordered[index]


def _ratio(hits, total):
    return round(hits / total, 4) if total else None


def run_evaluation(env, dataset_path, limit=None, pause_s=0.0, today=None):
    reference = _load_reference()
    today = today or date.today()
    items = [json.loads(line) for line in Path(dataset_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    if limit:
        items = items[:limit]

    orch = env["chatbot.orchestrator"]
    rows = []
    for index, item in enumerate(items):
        if index and pause_s:
            time.sleep(pause_s)  # respeta el límite de peticiones por minuto de la cuota gratuita
        print("[%s] %s" % (item["id"], item["query"]))
        result = orch.evaluate_query(item["query"])
        log = env["chatbot.query.log"].browse(result.get("log_id"))
        try:
            llm_entities = (json.loads(result.get("llm_json") or "{}") or {}).get("entities") or {}
        except json.JSONDecodeError:
            llm_entities = {}

        expected_intent = item.get("expected_intent")
        intent_ok = result.get("intent") == expected_intent if expected_intent else None
        entity_ok = entities_match(item.get("expected_entities"), llm_entities)
        behavior = behavior_ok(item, result)

        data_ok = None
        diffs = []
        texts_ok = None
        if item["expected_behavior"] == "execute":
            expected = reference.facts(env, item, today)
            diffs = reference.compare(expected, result.get("data") or {})
            texts_ok = all(contains_text(result.get("reply"), t) for t in item.get("expected_result_contains") or [])
            data_ok = behavior and not diffs and texts_ok

        rows.append({
            "id": item["id"],
            "category": item.get("category"),
            "query": item["query"],
            "expected_behavior": item["expected_behavior"],
            "expected_intent": expected_intent,
            "got_intent": result.get("intent"),
            "got_outcome": result.get("outcome"),
            "got_status": result.get("status"),
            "intent_ok": intent_ok,
            "entity_ok": entity_ok,
            "behavior_ok": behavior,
            "data_ok": data_ok,
            "texts_ok": texts_ok,
            "data_diffs": diffs,
            "provider_failure": result.get("outcome") == PROVIDER_FAILURE,
            "provider": log.llm_provider,
            "model": log.llm_model,
            "fallback_used": log.fallback_used,
            "latency_ms": result.get("latency_ms") or 0,
            "llm_ms": log.llm_ms,
            "orm_ms": log.orm_ms,
            "tokens_prompt": log.tokens_prompt,
            "tokens_output": log.tokens_output,
            "reply": result.get("reply"),
        })
    return summarize(rows), rows


def summarize(rows):
    def metric(key, subset=None):
        values = [r[key] for r in (subset if subset is not None else rows) if r[key] is not None]
        return {"aciertos": sum(values), "evaluadas": len(values), "porcentaje": _ratio(sum(values), len(values))}

    executes = [r for r in rows if r["expected_behavior"] == "execute"]
    by_category = {}
    for row in rows:
        cat = by_category.setdefault(row["category"], {"total": 0, "comportamiento_correcto": 0})
        cat["total"] += 1
        cat["comportamiento_correcto"] += int(row["behavior_ok"])
    latencies = [r["latency_ms"] for r in rows if not r["provider_failure"]]
    llm = [r["llm_ms"] for r in rows if not r["provider_failure"]]
    models = sorted({"%s/%s" % (r["provider"], r["model"]) for r in rows if r["model"]})
    return {
        "total_consultas": len(rows),
        "modelos": models,
        "intencion": metric("intent_ok"),
        "entidades": metric("entity_ok"),
        "comportamiento": metric("behavior_ok"),
        "ejecucion_con_datos_correctos": metric("data_ok", executes),
        "por_categoria": by_category,
        "fallos_del_proveedor": sum(r["provider_failure"] for r in rows),
        "respuestas_del_respaldo": sum(bool(r["fallback_used"]) for r in rows),
        "latencia_ms": {
            "mediana": int(statistics.median(latencies)) if latencies else 0,
            "p95": _percentile(latencies, 95),
            "promedio": int(statistics.mean(latencies)) if latencies else 0,
            "mediana_ia": int(statistics.median(llm)) if llm else 0,
        },
        "tokens_promedio": {
            "entrada": int(statistics.mean([r["tokens_prompt"] for r in rows])) if rows else 0,
            "salida": int(statistics.mean([r["tokens_output"] for r in rows])) if rows else 0,
        },
    }


# Ejecución directa dentro de `odoo shell` (el script de PowerShell lo importa y llama a run_evaluation).
if __name__ == "__main__" and "env" in globals():
    DATASET = "/tmp/eval_dataset.jsonl"
    summary, rows = run_evaluation(env, DATASET)  # noqa: F821
    Path("/tmp/eval_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    with Path("/tmp/eval_results.jsonl").open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    print("=== RESUMEN ===")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
