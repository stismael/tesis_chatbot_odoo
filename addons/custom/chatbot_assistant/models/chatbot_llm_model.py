# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _

from ..services import llm_client
from ..services.llm_client import DEFAULT_GEMINI_MODEL, DEFAULT_GROQ_MODEL

_logger = logging.getLogger(__name__)

PROVIDERS = [("gemini", "Google Gemini"), ("groq", "Groq")]
RECOMMENDED = {"gemini": DEFAULT_GEMINI_MODEL, "groq": DEFAULT_GROQ_MODEL}


class ChatbotLlmModel(models.Model):
    """Catálogo de modelos por proveedor, sincronizado con el listado de cada API."""

    _name = "chatbot.llm.model"
    _description = "Modelo de IA disponible"
    _order = "provider, recommended desc, model_id"
    _rec_name = "model_id"

    provider = fields.Selection(PROVIDERS, string="Proveedor", required=True, index=True)
    model_id = fields.Char(string="ID del modelo", required=True, index=True)
    display_name_api = fields.Char(string="Nombre")
    description = fields.Char(string="Descripción")
    input_token_limit = fields.Integer(string="Límite de tokens de entrada")
    output_token_limit = fields.Integer(string="Límite de tokens de salida")
    available = fields.Boolean(
        string="Disponible", default=True, index=True,
        help="Desmarcado cuando el proveedor ya no lo incluye en su listado.",
    )
    recommended = fields.Boolean(string="Recomendado", compute="_compute_recommended", store=True)
    last_seen = fields.Datetime(string="Visto en el listado")

    _sql_constraints = [
        ("provider_model_uniq", "unique(provider, model_id)", "El modelo ya está en el catálogo."),
    ]

    @api.depends("provider", "model_id")
    def _compute_recommended(self):
        for record in self:
            record.recommended = RECOMMENDED.get(record.provider) == record.model_id

    @api.depends("model_id", "recommended", "available")
    def _compute_display_name(self):
        for record in self:
            name = record.model_id or ""
            if record.recommended:
                name += _(" (recomendado)")
            if not record.available:
                name += _(" (no disponible)")
            record.display_name = name

    @api.model
    def _find(self, provider, model_id):
        return self.search([("provider", "=", provider), ("model_id", "=", model_id)], limit=1)

    @api.model
    def _sync_provider(self, provider, models_data):
        """
        Sincroniza el catálogo de un proveedor con su listado, sin borrar:
        agrega los nuevos, actualiza los existentes, marca "no disponible" a los que ya no
        aparecen y reactiva los que vuelven. Retorna los contadores.
        """
        now = fields.Datetime.now()
        existing = {m.model_id: m for m in self.search([("provider", "=", provider)])}
        counts = {"added": 0, "updated": 0, "unavailable": 0, "reactivated": 0}
        seen = set()
        for item in models_data:
            values = {
                "display_name_api": item.get("display_name") or item["id"],
                "description": item.get("description") or False,
                "input_token_limit": item.get("input_token_limit") or 0,
                "output_token_limit": item.get("output_token_limit") or 0,
                "available": True,
                "last_seen": now,
            }
            seen.add(item["id"])
            record = existing.get(item["id"])
            if record:
                if not record.available:
                    counts["reactivated"] += 1
                else:
                    counts["updated"] += 1
                record.write(values)
            else:
                self.create(dict(values, provider=provider, model_id=item["id"]))
                counts["added"] += 1
        gone = self.browse([m.id for mid, m in existing.items() if mid not in seen and m.available])
        gone.write({"available": False})
        counts["unavailable"] = len(gone)
        self.env["ir.config_parameter"].sudo().set_param(
            "chatbot_assistant.models_synced_%s" % provider, fields.Datetime.to_string(now),
        )
        return counts

    @api.model
    def _cron_sync_models(self):
        """Actualiza el catálogo del proveedor configurado (tarea semanal)."""
        config = llm_client.get_chatbot_config(self.env)
        if not config["api_key"]:
            return False
        try:
            models_data = llm_client.list_models(config)
        except llm_client.LLMClientError as exc:
            _logger.warning("Chatbot: no se pudo actualizar el catálogo de modelos: %s", exc.admin_message)
            return False
        return self._sync_provider(config["provider"], models_data)
