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


if __name__ == "__main__":
    test_ready_factura()
    test_missing_stock()
    test_reject_unknown_intent()
    test_merge_pending()
    test_dataset_loads()
    test_http_error_mapping()
    print("OK: validator + dataset + LLM error mapping checks passed")
