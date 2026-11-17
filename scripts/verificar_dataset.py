# -*- coding: utf-8 -*-
"""
Verifica el dataset de evaluación contra los datos de Odoo, sin llamar a la IA.

Para cada consulta "execute" ejecuta la función interna del asistente con las entidades esperadas
y compara sus datos con la referencia independiente (eval_reference.py: consultas directas al ORM
y campos nativos de Odoo). También revisa los textos esperados sin aceptar negaciones
(«pagada» no coincide con «no pagada»).

Uso (con la base ya generada), desde la raíz del proyecto:
    docker cp .\data\eval\eval_dataset.jsonl odoo18-chatbot-odoo:/tmp/eval_dataset.jsonl
    docker cp .\scripts\eval_reference.py odoo18-chatbot-odoo:/tmp/eval_reference.py
    docker cp .\scripts\chatbot_eval_runner.py odoo18-chatbot-odoo:/tmp/chatbot_eval_runner.py
    Get-Content .\scripts\verificar_dataset.py | docker compose exec -T odoo odoo shell -d <base> --no-http
Variable opcional DATASET con otra ruta del archivo dentro del contenedor.
"""
import importlib.util
import json
import os
from datetime import date

from odoo.addons.chatbot_assistant.services.handlers import HANDLER_MAP
from odoo.addons.chatbot_assistant.services.validator import validate_llm_output

DATASET = os.environ.get("DATASET", "/tmp/eval_dataset.jsonl")


def _load(name):
    spec = importlib.util.spec_from_file_location(name, "/tmp/%s.py" % name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


reference = _load("eval_reference")
runner = _load("chatbot_eval_runner")

SaleOrder = env["sale.order"]  # noqa: F821 (env lo define odoo shell)
print("Pedidos de venta:", SaleOrder.search_count([]),
      {s: SaleOrder.search_count([("state", "=", s)]) for s in ("draft", "sent", "sale", "cancel")})
print("Facturas de cliente:", env["account.move"].search_count([("move_type", "=", "out_invoice")]))  # noqa: F821

failures = 0
checked = 0
with open(DATASET, encoding="utf-8") as fh:
    for line in fh:
        if not line.strip():
            continue
        item = json.loads(line)
        if item.get("expected_behavior") != "execute":
            continue
        checked += 1
        expected = reference.facts(env, item)  # noqa: F821
        validated = validate_llm_output({
            "intent": item["expected_intent"], "entities": item["expected_entities"], "status": "ready",
        })
        entities = dict(validated["entities"])
        if item.get("expected_period"):
            date_from, date_to = reference._period(item, date.today())
            entities.update(date_from=date_from.isoformat(), date_to=date_to.isoformat())
        result = HANDLER_MAP[validated["intent"]](env, entities, user_text=item["query"])  # noqa: F821
        diffs = reference.compare(expected, result.get("data") or {})
        missing = [t for t in item.get("expected_result_contains") or []
                   if not runner.contains_text(result.get("message"), t)]
        if diffs or missing:
            failures += 1
            print("NO CUMPLE", item["id"], diffs, missing, "|", (result.get("message") or "")[:160].replace("\n", " "))
print("Consultas verificadas: %s · no cumplen: %s" % (checked, failures))
