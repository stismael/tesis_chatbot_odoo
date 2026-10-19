# -*- coding: utf-8 -*-
"""
Runner de evaluación del chatbot (Capítulo 5).

Uso dentro del contenedor Odoo:
  odoo shell -d odoo18_chatbot < /mnt/extra-addons/../..  (mejor vía script host)

Desde el host (PowerShell):
  .\\scripts\\run-chatbot-eval.ps1

Requiere API key configurada en Ajustes → Chatbot asistente.
"""
import json
import sys
from pathlib import Path


def _entity_match(expected, actual):
    if not expected:
        return True
    actual = actual or {}
    for key, value in expected.items():
        if value is None:
            continue
        got = actual.get(key)
        if got is None:
            return False
        if str(value).strip().lower() not in str(got).strip().lower() and str(got).strip().lower() not in str(value).strip().lower():
            # permitir igualdad exacta casefold
            if str(value).casefold() != str(got).casefold():
                return False
    return True


def _behavior_ok(item, result, llm_entities):
    behavior = item.get("expected_behavior")
    intent = result.get("intent")
    status = result.get("status")
    reply = (result.get("reply") or "").lower()
    expected_intent = item.get("expected_intent")

    intent_ok = intent == expected_intent

    if behavior == "execute":
        contains = item.get("expected_result_contains") or []
        text_ok = all(c.lower() in reply for c in contains)
        exec_ok = bool(result.get("success")) and status in ("ready", None) or text_ok
        # Si el handler respondió con datos, status puede ser ready implícito
        if contains and text_ok and intent_ok:
            return True, intent_ok, True, True
        return intent_ok and text_ok, intent_ok, _entity_match(item.get("expected_entities"), llm_entities), text_ok

    if behavior == "clarify":
        ok = intent_ok and status in ("missing_information", "ambiguous")
        return ok, intent_ok, True, ok

    if behavior == "reject":
        ok = intent == "fuera_de_alcance" or status == "rejected"
        # también aceptar si el texto indica fuera de alcance
        if "fuera del alcance" in reply:
            ok = True
        return ok, intent == "fuera_de_alcance" or ok, True, ok

    if behavior == "converse":
        # La IA responde con sus palabras y sin cifras (el validador descarta las que las traen).
        ok = intent == "conversacion" and bool(reply) and not any(ch.isdigit() for ch in reply)
        return ok, intent == "conversacion", True, ok

    if behavior == "not_conversation":
        # Pregunta de datos escrita como charla: debe ir por una intención de consulta.
        ok = intent not in ("conversacion", "fuera_de_alcance")
        return ok, ok, True, ok

    if behavior in ("clarify_or_not_found", "clarify_or_execute", "reject_or_clarify"):
        return True, intent_ok or intent == "fuera_de_alcance", True, True

    return intent_ok, intent_ok, _entity_match(item.get("expected_entities"), llm_entities), bool(result.get("success"))


def run_evaluation(env, dataset_path, limit=None):
    path = Path(dataset_path)
    items = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    if limit:
        items = items[:limit]

    orch = env["chatbot.orchestrator"]
    rows = []
    intent_hits = 0
    entity_hits = 0
    exec_hits = 0
    total_latency = 0

    for item in items:
        qid = item["id"]
        query = item["query"]
        print(f"[{qid}] {query}")
        result = orch.evaluate_query(query)
        llm_entities = {}
        if result.get("llm_json"):
            try:
                parsed = json.loads(result["llm_json"])
                llm_entities = parsed.get("entities") or {}
            except json.JSONDecodeError:
                llm_entities = {}

        overall, intent_ok, entity_ok, exec_ok = _behavior_ok(item, result, llm_entities)
        if intent_ok:
            intent_hits += 1
        if entity_ok:
            entity_hits += 1
        if exec_ok or overall:
            exec_hits += 1
        total_latency += result.get("latency_ms") or 0

        rows.append({
            "id": qid,
            "category": item.get("category"),
            "query": query,
            "expected_intent": item.get("expected_intent"),
            "got_intent": result.get("intent"),
            "got_status": result.get("status"),
            "intent_ok": intent_ok,
            "entity_ok": entity_ok,
            "exec_ok": exec_ok,
            "overall_ok": overall,
            "latency_ms": result.get("latency_ms"),
            "reply": result.get("reply"),
        })

    n = len(items) or 1
    summary = {
        "total": len(items),
        "intent_accuracy": round(intent_hits / n, 4),
        "entity_accuracy": round(entity_hits / n, 4),
        "execution_accuracy": round(exec_hits / n, 4),
        "avg_latency_ms": int(total_latency / n),
        "intent_hits": intent_hits,
        "entity_hits": entity_hits,
        "exec_hits": exec_hits,
    }
    return summary, rows


# Auto-ejecución solo cuando se carga dentro de `odoo shell` como script stdin.
# Evitar side-effects al importarse desde run-chatbot-eval.ps1.
if __name__ == "__main__" and "env" in globals():
    DATASET = "/tmp/eval_dataset.jsonl"
    for candidate in (
        DATASET,
        "/mnt/eval/eval_dataset.jsonl",
    ):
        if Path(candidate).exists():
            DATASET = candidate
            break
    summary, rows = run_evaluation(env, DATASET)  # noqa: F821
    out_dir = Path("/tmp")
    (out_dir / "eval_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    with (out_dir / "eval_results.jsonl").open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("=== SUMMARY ===")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
