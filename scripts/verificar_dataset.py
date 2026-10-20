# -*- coding: utf-8 -*-
"""
Verifica el dataset de evaluación contra los datos reales de Odoo, sin llamar a la IA.

Para cada consulta "execute" ejecuta el handler con las entidades esperadas y revisa que la
respuesta contenga los textos de `expected_result_contains`. Sirve para comprobar que la base
de prueba (módulo chatbot_test_data) coincide con lo que espera el dataset.

Uso (con la base ya generada), desde la raíz del proyecto:
    docker cp .\data\eval\eval_dataset.jsonl odoo18-chatbot-odoo:/tmp/eval_dataset.jsonl
    Get-Content .\scripts\verificar_dataset.py | docker compose exec -T odoo odoo shell -d <base> --no-http
Variable opcional DATASET con otra ruta del archivo dentro del contenedor.
"""
import json
import os

from odoo.addons.chatbot_assistant.services.handlers import HANDLER_MAP
from odoo.addons.chatbot_assistant.services.validator import validate_llm_output

DATASET = os.environ.get("DATASET", "/tmp/eval_dataset.jsonl")

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
        validated = validate_llm_output({
            "intent": item["expected_intent"], "entities": item["expected_entities"], "status": "ready",
        })
        result = HANDLER_MAP[validated["intent"]](env, validated["entities"], user_text=item["query"])  # noqa: F821
        message = (result.get("message") or "").lower()
        missing = [text for text in item.get("expected_result_contains") or [] if text.lower() not in message]
        if missing:
            failures += 1
            print("NO CUMPLE", item["id"], missing, "|", message[:160].replace("\n", " "))
print("Consultas verificadas: %s · no cumplen: %s" % (checked, failures))
