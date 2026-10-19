# -*- coding: utf-8 -*-
import json
import logging
import time

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError

from ..services import llm_client
from ..services.handlers import HANDLER_MAP
from ..services.prompt_builder import RESPONSE_SCHEMA, SYSTEM_PROMPT, build_user_payload
from ..services.validator import merge_pending_entities, validate_llm_output, enrich_entities_from_session

from ..services.llm_client import USER_MESSAGES, ChatbotLLMError

_logger = logging.getLogger(__name__)

MISSING_LABELS = {
    "invoice_number": "el número de factura (ej. INV/2026/00001)",
    "customer_name": "el nombre del cliente",
    "product_name": "el nombre del producto",
    "product_code": "el código del producto",
    "location_name": "la ubicación",
    "date_from": "la fecha desde",
    "date_to": "la fecha hasta",
}

FORBIDDEN_AREA_MSG = "No tienes permiso para consultar %s. Pide acceso al administrador."

FORBIDDEN_MSG = (
    "No tienes permiso para consultar esa información. "
    "Pide acceso al administrador."
)

# Códigos de error de la IA que indican una respuesta defectuosa (no una caída del servicio).
LLM_BAD_OUTPUT_CODES = ("invalid_json", "bad_response", "blocked")

OUT_OF_SCOPE_MSG = (
    "Esa solicitud está fuera del alcance del asistente. "
    "Solo puedo consultar facturas, inventario, ventas por cliente o producto, "
    "vendedor asignado y stock con facturación por producto. "
    "No puedo crear ni modificar registros."
)


class ChatbotOrchestrator(models.AbstractModel):
    _name = "chatbot.orchestrator"
    _description = "Orquestador del asistente conversacional"

    @api.model
    def process_message(self, session, user_text):
        """Procesa un mensaje de usuario y retorna dict con reply/intent/status."""
        started = time.perf_counter()
        intent = None
        status = None
        llm_json = None
        reply = None
        success = False
        error = None
        handler_data = {}
        outcome = None
        error_code = None
        llm_ms = 0
        orm_ms = 0
        llm_meta = {}

        try:
            context = session.get_short_context()
            today = fields.Date.context_today(self).isoformat()
            user_payload = build_user_payload(user_text, context, today=today)
            llm_started = time.perf_counter()
            try:
                raw = llm_client.complete_json(
                    self.env, SYSTEM_PROMPT, user_payload, meta=llm_meta, response_schema=RESPONSE_SCHEMA,
                )
            finally:
                llm_ms = int((time.perf_counter() - llm_started) * 1000)
            llm_json = json.dumps(raw, ensure_ascii=False)
            validated = validate_llm_output(raw)

            # Completar entidades desde la sesión (preguntas de seguimiento: "este producto", etc.)
            last_entities = session.get_pending_entities()
            enriched = enrich_entities_from_session(
                validated["entities"], validated["intent"], last_entities,
            )
            if enriched != validated["entities"]:
                validated["entities"] = enriched
                revalidated = validate_llm_output({
                    "intent": validated["intent"],
                    "entities": enriched,
                    "status": "ready",
                    "missing_entities": [],
                })
                validated = revalidated

            # Fusionar con la memoria corta si hay una consulta pendiente
            pending_entities = session.get_pending_entities()
            if session.pending_intent and validated["intent"] in (
                session.pending_intent,
                "consultar_factura",
                "consultar_stock",
                "consultar_ventas_cliente",
                "consultar_vendedor_cliente",
                "consultar_stock_facturacion_producto",
            ):
                # Si el usuario solo aclara una entidad, conservar la intención pendiente
                if validated["status"] in ("ready", "missing_information", "ambiguous"):
                    if not validated.get("entities") or self._mostly_empty(validated["entities"]):
                        validated["intent"] = session.pending_intent
                    merged = merge_pending_entities(pending_entities, validated["entities"])
                    validated["entities"] = merged
                    # Revalidar las entidades requeridas
                    revalidated = validate_llm_output({
                        "intent": validated["intent"] if validated["intent"] != "fuera_de_alcance" else session.pending_intent,
                        "entities": merged,
                        "status": "ready",
                        "missing_entities": [],
                    })
                    validated = revalidated

            intent = validated["intent"]
            status = validated["status"]

            # Permisos por consulta: se revisan antes de ejecutar y antes de pedir datos faltantes.
            missing_groups, permission = self.env["chatbot.intent.permission"]._missing_groups(intent)
            if intent in HANDLER_MAP and status != "invalid_output" and missing_groups:
                session.clear_pending()
                reply = FORBIDDEN_AREA_MSG % permission.area_label
                error = "Faltan grupos: %s" % ", ".join(missing_groups.mapped("full_name"))
                success = False
                outcome, error_code = "forbidden", "intent_permission"
            elif intent == "fuera_de_alcance" or status == "rejected":
                session.clear_pending()
                reply = OUT_OF_SCOPE_MSG
                success = True
                if validated.get("error") == "unknown_intent":
                    outcome, error_code = "llm_bad_output", "unknown_intent"
                else:
                    outcome = "rejected"
            elif status == "invalid_output":
                session.clear_pending()
                reply = _("No pude interpretar la consulta. Reformule la pregunta, por favor.")
                success = False
                error = validated.get("error") or "invalid_output"
                outcome, error_code = "llm_bad_output", "invalid_output"
            elif status == "ambiguous":
                session.set_pending(intent, validated["entities"])
                reply = _("La consulta es ambigua. Precise el cliente, producto o factura.")
                success = True
                outcome = "clarification"
            elif status == "missing_information":
                session.set_pending(intent, validated["entities"])
                missing = validated.get("missing_entities") or []
                labels = [MISSING_LABELS.get(m, m) for m in missing]
                if labels:
                    reply = _("Para continuar, indique: %s.") % " o ".join(labels)
                else:
                    reply = _("Falta información para ejecutar la consulta. Precise los datos.")
                success = True
                outcome = "clarification"
            elif status == "ready":
                handler = HANDLER_MAP.get(intent)
                if not handler:
                    session.clear_pending()
                    reply = OUT_OF_SCOPE_MSG
                    intent = "fuera_de_alcance"
                    status = "rejected"
                    success = True
                    outcome = "rejected"
                else:
                    orm_started = time.perf_counter()
                    try:
                        result = handler(self.env, validated["entities"], user_text=user_text)
                    finally:
                        orm_ms = int((time.perf_counter() - orm_started) * 1000)
                    handler_data = result.get("data") or {}
                    if result.get("status") == "ambiguous":
                        session.set_pending(intent, validated["entities"])
                        status = "ambiguous"
                        reply = result.get("message")
                        success = True
                        outcome = "clarification"
                    elif result.get("ok"):
                        session.clear_pending()
                        # Guardar las últimas entidades para preguntas de seguimiento
                        session.set_pending(False, validated["entities"])
                        session.pending_intent = False
                        reply = result.get("message")
                        success = True
                        outcome = "answered"
                    else:
                        # No encontrado / datos insuficientes del handler
                        if "Indique" in (result.get("message") or ""):
                            session.set_pending(intent, validated["entities"])
                            status = "missing_information"
                            outcome = "clarification"
                        else:
                            outcome = "no_results"
                        reply = result.get("message") or _("No se encontraron datos.")
                        success = bool(result.get("ok"))
            else:
                reply = _("No pude procesar la consulta.")
                success = False
                outcome = "internal_error"

        except AccessError as exc:
            # Odoo negó el acceso a un modelo o registro: mensaje en español, detalle solo en el log.
            reply = FORBIDDEN_MSG
            error = str(exc)[:500]
            success = False
            status = status or "error"
            outcome, error_code = "forbidden", "access"
        except ChatbotLLMError as exc:
            reply = exc.args[0] if exc.args else str(exc)
            error = reply
            success = False
            status = status or "error"
            error_code = exc.code if exc.code in dict(self._error_codes()) else "generic"
            outcome = "llm_bad_output" if error_code in LLM_BAD_OUTPUT_CODES else "llm_unavailable"
        except UserError as exc:
            # Mensaje ya pensado para el usuario final (sin jerga HTTP/timeout).
            reply = exc.args[0] if exc.args else str(exc)
            error = reply
            success = False
            status = status or "error"
            outcome, error_code = "internal_error", "generic"
        except Exception as exc:
            _logger.exception("Error en orquestador chatbot")
            error = str(exc)
            reply = USER_MESSAGES["generic"]
            success = False
            status = status or "error"
            outcome, error_code = "internal_error", "generic"

        latency_ms = int((time.perf_counter() - started) * 1000)
        log = self.env["chatbot.query.log"].sudo().create({
            "name": (user_text or "")[:80],
            "user_id": self.env.user.id,
            "session_id": session.id,
            "query": user_text,
            "intent": intent,
            "status": status,
            "llm_json": llm_json,
            "reply": reply,
            "success": success,
            "latency_ms": latency_ms,
            "error": error,
            "handler_data_json": json.dumps(handler_data, ensure_ascii=False, default=str),
            "outcome": outcome,
            "error_code": error_code,
            "llm_ms": llm_ms,
            "orm_ms": orm_ms,
            "retries": llm_meta.get("retries", 0),
            "llm_provider": llm_meta.get("provider"),
            "llm_model": llm_meta.get("model"),
            "tokens_prompt": llm_meta.get("tokens_prompt", 0),
            "tokens_output": llm_meta.get("tokens_output", 0),
            "tokens_thinking": llm_meta.get("tokens_thinking", 0),
        })

        return {
            "reply": reply,
            "intent": intent,
            "status": status,
            "success": success,
            "latency_ms": latency_ms,
            "data": handler_data,
            "llm_json": llm_json,
            "outcome": outcome,
            "log_id": log.id,
        }

    @api.model
    def _error_codes(self):
        return self.env["chatbot.query.log"]._fields["error_code"].selection

    @api.model
    def _mostly_empty(self, entities):
        return not any(entities.get(k) for k in (entities or {}))

    @api.model
    def evaluate_query(self, query_text, session=None):
        """API usada por el runner de evaluación (sin UI)."""
        if session is None:
            session = self.env["chatbot.session"].create({
                "name": _("Eval: %s") % (query_text[:40],),
            })
        self.env["chatbot.message"].create({
            "session_id": session.id,
            "role": "user",
            "body": query_text,
        })
        result = self.process_message(session, query_text)
        self.env["chatbot.message"].create({
            "session_id": session.id,
            "role": "assistant",
            "body": result.get("reply") or "",
            "intent": result.get("intent"),
            "status": result.get("status"),
        })
        return result
