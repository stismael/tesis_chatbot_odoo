# -*- coding: utf-8 -*-
"""Validación sintáctica y semántica de la salida JSON del LLM."""

import datetime

from .prompt_builder import ALLOWED_INTENTS, ENTITY_KEYS

DATE_KEYS = ("date_from", "date_to")

# Cada intención tiene grupos OR: basta con satisfacer UN grupo.
# Dentro de un grupo, basta con UNA entidad (OR interno).
REQUIRED_BY_INTENT = {
    "consultar_factura": (("invoice_number",), ("customer_name",)),
    "consultar_stock": (("product_name", "product_code"),),
    "consultar_ventas_cliente": (("customer_name",), ("product_name", "product_code")),
    "consultar_vendedor_cliente": (("customer_name",),),
    "consultar_stock_facturacion_producto": (("product_name", "product_code"),),
    "fuera_de_alcance": (),
}

ALLOWED_STATUS = {
    "ready",
    "missing_information",
    "ambiguous",
    "rejected",
    "invalid_output",
}


def _clean_entities(raw_entities):
    entities = {}
    raw = raw_entities if isinstance(raw_entities, dict) else {}
    for key in ENTITY_KEYS:
        value = raw.get(key)
        if value is None or value == "" or value == "null":
            entities[key] = None
        elif key in DATE_KEYS:
            entities[key] = _normalize_date(value)
        else:
            entities[key] = str(value).strip()
    return entities


def _normalize_date(value):
    """Acepta solo fechas ISO (AAAA-MM-DD); cualquier otro texto se descarta."""
    try:
        return datetime.date.fromisoformat(str(value).strip()[:10]).isoformat()
    except ValueError:
        return None


def _has_required(entities, intent):
    groups = REQUIRED_BY_INTENT.get(intent, ())
    if not groups:
        return True, []
    for group in groups:
        if any(entities.get(k) for k in group):
            return True, []
    missing = []
    for group in groups:
        for key in group:
            if key not in missing:
                missing.append(key)
    return False, missing


def validate_llm_output(data):
    """
    Valida y normaliza la salida del LLM.
    Retorna dict:
      ok, intent, entities, status, missing_entities, error
    """
    if not isinstance(data, dict):
        return {
            "ok": False,
            "intent": "fuera_de_alcance",
            "entities": _clean_entities({}),
            "status": "invalid_output",
            "missing_entities": [],
            "error": "not_a_dict",
        }

    intent = data.get("intent")
    if intent not in ALLOWED_INTENTS:
        return {
            "ok": False,
            "intent": "fuera_de_alcance",
            "entities": _clean_entities(data.get("entities")),
            "status": "rejected",
            "missing_entities": [],
            "error": "unknown_intent",
        }

    entities = _clean_entities(data.get("entities"))
    status = data.get("status") or "ready"
    if status not in ALLOWED_STATUS:
        status = "invalid_output"

    missing = data.get("missing_entities") or []
    if not isinstance(missing, list):
        missing = []
    missing = [str(x) for x in missing]

    if intent == "fuera_de_alcance":
        return {
            "ok": True,
            "intent": intent,
            "entities": entities,
            "status": "rejected",
            "missing_entities": [],
            "error": None,
        }

    ok_req, computed_missing = _has_required(entities, intent)
    if not ok_req:
        return {
            "ok": True,
            "intent": intent,
            "entities": entities,
            "status": "missing_information",
            "missing_entities": computed_missing or missing,
            "error": None,
        }

    if status in ("missing_information", "ambiguous", "rejected", "invalid_output"):
        return {
            "ok": True,
            "intent": intent,
            "entities": entities,
            "status": status,
            "missing_entities": missing,
            "error": None,
        }

    return {
        "ok": True,
        "intent": intent,
        "entities": entities,
        "status": "ready",
        "missing_entities": [],
        "error": None,
    }


def merge_pending_entities(pending, new_entities):
    """Combina entidades pendientes de sesión con las nuevas (prioridad a no-nulas nuevas)."""
    merged = dict(pending or {})
    for key in ENTITY_KEYS:
        new_val = (new_entities or {}).get(key)
        if new_val:
            merged[key] = new_val
        elif key not in merged:
            merged[key] = None
    return _clean_entities(merged)


def enrich_entities_from_session(entities, intent, last_entities):
    """Completa entidades faltantes desde la sesión (follow-ups como 'este producto')."""
    if not last_entities or intent not in REQUIRED_BY_INTENT:
        return _clean_entities(entities)

    merged = _clean_entities(entities)
    ok_req, _missing = _has_required(merged, intent)
    if ok_req:
        return merged

    for key in ENTITY_KEYS:
        if not merged.get(key) and last_entities.get(key):
            merged[key] = last_entities[key]

    return _clean_entities(merged)
