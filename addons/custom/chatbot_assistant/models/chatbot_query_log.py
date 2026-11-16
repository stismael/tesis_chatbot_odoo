# -*- coding: utf-8 -*-
import json
import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError

_logger = logging.getLogger(__name__)

OUTCOMES = [
    ("answered", "Respondida con datos"),
    ("no_results", "Sin resultados"),
    ("clarification", "Aclaración pedida"),
    ("conversation", "Conversación"),
    ("rejected", "Rechazada (fuera de alcance)"),
    ("forbidden", "Sin permiso"),
    ("llm_unavailable", "IA no disponible"),
    ("llm_bad_output", "IA respondió mal"),
    ("internal_error", "Error interno"),
]

ERROR_CODES = [
    ("timeout", "Tiempo de espera agotado"),
    ("network", "Sin conexión"),
    ("rate_limit", "Cuota agotada (429)"),
    ("server", "Servicio caído (5xx)"),
    ("auth", "API key inválida"),
    ("forbidden_network", "Bloqueo de red del proveedor (403)"),
    ("model", "Modelo inexistente"),
    ("blocked", "Respuesta bloqueada"),
    ("invalid_json", "JSON inválido"),
    ("bad_response", "Respuesta inesperada"),
    ("invalid_output", "Salida no válida"),
    ("unknown_intent", "Intención inventada"),
    ("reply_discarded", "Respuesta redactada descartada (cifras)"),
    ("inactive", "Asistente desactivado"),
    ("missing_key", "API key no configurada"),
    ("intent_permission", "Sin el grupo exigido para la consulta"),
    ("access", "Permiso denegado por Odoo"),
    ("generic", "Otro"),
]

THUMBS_UP = "\U0001F44D"
THUMBS_DOWN = "\U0001F44E"


class ChatbotQueryLog(models.Model):
    _name = "chatbot.query.log"
    _description = "Auditoría de consultas del chatbot"
    _order = "create_date desc, id desc"

    name = fields.Char(string="Resumen", required=True)
    user_id = fields.Many2one("res.users", string="Usuario", required=True, index=True)
    session_id = fields.Many2one("chatbot.session", string="Sesión", ondelete="set null", index=True)
    query = fields.Text(string="Pregunta", required=True)
    intent = fields.Char(string="Intención", index=True)
    status = fields.Char(string="Estado", index=True)
    llm_json = fields.Text(string="JSON de la IA")
    reply = fields.Text(string="Respuesta")
    success = fields.Boolean(string="Éxito", default=False)
    error = fields.Char(string="Detalle del error")
    handler_data_json = fields.Text(string="Datos de Odoo")

    outcome = fields.Selection(OUTCOMES, string="Resultado", index=True)
    error_code = fields.Selection(ERROR_CODES, string="Código de error", index=True)

    latency_ms = fields.Integer(string="Tiempo total (ms)", aggregator="avg")
    llm_ms = fields.Integer(string="Tiempo IA (ms)", aggregator="avg")
    orm_ms = fields.Integer(string="Tiempo Odoo (ms)", aggregator="avg")
    retries = fields.Integer(string="Reintentos", aggregator="sum")

    llm_provider = fields.Char(string="Proveedor", index=True)
    llm_model = fields.Char(string="Modelo", index=True)
    fallback_used = fields.Boolean(
        string="Respondió el respaldo", index=True,
        help="El modelo principal no estaba disponible y respondió el modelo de respaldo.",
    )
    primary_error_code = fields.Selection(ERROR_CODES, string="Fallo del modelo principal")
    tokens_prompt = fields.Integer(string="Tokens de entrada")
    tokens_output = fields.Integer(string="Tokens de salida")
    tokens_thinking = fields.Integer(string="Tokens de razonamiento")
    # Resultado extenso: todos los registros de la respuesta, para «Ver todo» y la descarga en CSV.
    result_model = fields.Char(string="Modelo del resultado")
    result_ids_json = fields.Text(string="Registros del resultado")
    result_title = fields.Char(string="Título del resultado")
    result_count = fields.Integer(string="Registros en el resultado")
    result_views = fields.Integer(string="Veces que abrió «Ver todo»", aggregator="sum")
    csv_downloads = fields.Integer(string="Descargas CSV", aggregator="sum")
    last_csv_download = fields.Datetime(string="Última descarga CSV")

    reply_message_id = fields.Many2one(
        "mail.message", string="Mensaje de respuesta", ondelete="set null", index=True,
    )
    user_feedback = fields.Selection(
        [("up", "👍 Útil"), ("down", "👎 No útil")],
        string="Valoración", index=True,
    )

    @api.model
    def _update_feedback_from_messages(self, messages):
        """Recalcula la valoración 👍/👎 de los logs ligados a esos mensajes del bot."""
        if not messages:
            return
        logs = self.sudo().search([("reply_message_id", "in", messages.ids)])
        for log in logs:
            contents = log.reply_message_id.sudo().reaction_ids.mapped("content")
            if any(c.startswith(THUMBS_DOWN) for c in contents):
                feedback = "down"
            elif any(c.startswith(THUMBS_UP) for c in contents):
                feedback = "up"
            else:
                feedback = False
            if log.user_feedback != feedback:
                log.user_feedback = feedback

    def _result_records(self):
        """
        Registros del resultado leídos con el usuario actual: Odoo vuelve a aplicar sus permisos y
        reglas, así que solo aparecen los que todavía puede ver.
        """
        self.ensure_one()
        if not self.exists():
            raise UserError(_("Este resultado ya no está disponible."))
        try:
            self.check_access("read")
        except AccessError:
            raise UserError(_("Este resultado pertenece a la consulta de otro usuario.")) from None
        if not self.result_model or self.result_model not in self.env:
            raise UserError(_("Esta respuesta no tiene un resultado para mostrar."))
        ids = json.loads(self.result_ids_json or "[]")
        return self.env[self.result_model].search([("id", "in", ids)])

    def action_open_result(self):
        """«Ver todo»: abre la lista nativa de Odoo con los registros exactos de la respuesta."""
        records = self._result_records()
        self.sudo().result_views += 1
        return {
            "type": "ir.actions.act_window",
            "name": self.result_title or _("Resultado del asistente"),
            "res_model": records._name,
            "views": [[False, "list"], [False, "form"]],
            "domain": [("id", "in", records.ids)],
            "context": {"create": False},
            "target": "current",
        }

    @api.model
    def _cron_purge_old_logs(self):
        """Borra registros más antiguos que los días configurados (0 = conservar todo)."""
        raw = self.env["ir.config_parameter"].sudo().get_param(
            "chatbot_assistant.log_retention_days", "0",
        )
        try:
            days = int(raw or 0)
        except ValueError:
            days = 0
        if days <= 0:
            return 0
        limit = fields.Datetime.now() - timedelta(days=days)
        old = self.sudo().search([("create_date", "<", limit)])
        count = len(old)
        old.unlink()
        _logger.info("Chatbot: %s registros de auditoría eliminados (más de %s días)", count, days)
        return count
