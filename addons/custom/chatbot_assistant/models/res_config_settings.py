# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

from ..services import llm_client
from ..services.llm_client import DEFAULT_GEMINI_MODEL, DEFAULT_GROQ_MODEL, LLMClientError


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    chatbot_active = fields.Boolean(
        string="Chatbot activo",
        config_parameter="chatbot_assistant.active",
        default=True,
    )
    chatbot_provider = fields.Selection(
        selection=[
            ("gemini", "Google Gemini"),
            ("groq", "Groq"),
        ],
        string="Proveedor LLM",
        config_parameter="chatbot_assistant.provider",
        default="gemini",
    )
    chatbot_api_key = fields.Char(
        string="API Key",
        config_parameter="chatbot_assistant.api_key",
        groups="base.group_system,chatbot_assistant.group_chatbot_manager",
    )
    chatbot_model = fields.Char(
        string="Modelo",
        config_parameter="chatbot_assistant.model",
        default=DEFAULT_GEMINI_MODEL,
        help="ID técnico del modelo (ej. gemini-2.5-flash). Use 'Listar modelos' para ver opciones vigentes.",
    )
    chatbot_temperature = fields.Float(
        string="Temperature",
        config_parameter="chatbot_assistant.temperature",
        default=0.1,
    )
    chatbot_timeout = fields.Integer(
        string="Timeout (segundos)",
        config_parameter="chatbot_assistant.timeout",
        default=45,
    )

    chatbot_log_retention_days = fields.Integer(
        string="Conservar auditoría (días)",
        config_parameter="chatbot_assistant.log_retention_days",
        default=0,
        help="Los registros de auditoría más antiguos se borran cada día. 0 = conservar todo.",
    )

    def _chatbot_runtime_config(self):
        """Config desde el formulario; si la key viene vacía, usa la guardada en ICP."""
        self.ensure_one()
        api_key = (self.chatbot_api_key or "").strip()
        if not api_key:
            api_key = self.env["ir.config_parameter"].sudo().get_param(
                "chatbot_assistant.api_key", ""
            ) or ""
        provider = self.chatbot_provider or "gemini"
        default_model = DEFAULT_GEMINI_MODEL if provider == "gemini" else DEFAULT_GROQ_MODEL
        return {
            "provider": provider,
            "api_key": api_key,
            "model": (self.chatbot_model or default_model).strip(),
            "temperature": self.chatbot_temperature if self.chatbot_temperature is not None else 0.1,
            "timeout": self.chatbot_timeout or 45,
        }

    def action_chatbot_list_models(self):
        self.ensure_one()
        config = self._chatbot_runtime_config()
        try:
            models = llm_client.list_models(config)
        except LLMClientError as exc:
            raise UserError(exc.admin_message or exc.message) from exc

        suggested = llm_client.suggest_default_model(models, config["provider"])
        lines = [
            _("Proveedor: %s") % ("Groq" if config["provider"] == "groq" else "Google Gemini"),
            _("Modelos con generateContent / chat (%s):") % len(models),
            "",
        ]
        for m in models[:80]:
            mark = " ← recomendado" if m["id"] == suggested else ""
            lines.append("- %s%s" % (m["id"], mark))
        if len(models) > 80:
            lines.append(_("… y %s más") % (len(models) - 80))
        lines.append("")
        lines.append(_("Sugerido: %s") % suggested)
        body = "\n".join(lines)

        self.env["ir.config_parameter"].sudo().set_param(
            "chatbot_assistant.models_info",
            body,
        )

        wizard = self.env["chatbot.llm.result.wizard"].create({
            "title": _("Modelos disponibles (%s)") % len(models),
            "body": body,
            "suggested_model": suggested,
        })
        return {
            "type": "ir.actions.act_window",
            "name": _("Modelos disponibles"),
            "res_model": "chatbot.llm.result.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_chatbot_test_connection(self):
        self.ensure_one()
        config = self._chatbot_runtime_config()
        try:
            result = llm_client.test_connection(config)
        except LLMClientError as exc:
            raise UserError(exc.admin_message or exc.message) from exc

        info = _(
            "✓ Conexión exitosa\n"
            "Proveedor: %(provider)s\n"
            "Modelo: %(model)s\n"
            "Latencia: %(latency)s ms\n"
            "Estado: Disponible"
        ) % {
            "provider": result["provider"],
            "model": result["model"],
            "latency": result["latency_ms"],
        }
        self.env["ir.config_parameter"].sudo().set_param(
            "chatbot_assistant.last_test_info",
            info,
        )
        wizard = self.env["chatbot.llm.result.wizard"].create({
            "title": _("Prueba de conexión"),
            "body": info,
            "suggested_model": False,
        })
        return {
            "type": "ir.actions.act_window",
            "name": _("Prueba de conexión"),
            "res_model": "chatbot.llm.result.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    @api.onchange("chatbot_provider")
    def _onchange_chatbot_provider(self):
        if self.chatbot_provider == "groq":
            if not self.chatbot_model or "gemini" in (self.chatbot_model or ""):
                self.chatbot_model = DEFAULT_GROQ_MODEL
        elif self.chatbot_provider == "gemini":
            if not self.chatbot_model or "llama" in (self.chatbot_model or "") or "groq" in (self.chatbot_model or ""):
                self.chatbot_model = DEFAULT_GEMINI_MODEL
