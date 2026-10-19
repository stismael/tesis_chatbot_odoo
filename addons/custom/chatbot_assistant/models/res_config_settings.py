# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

from ..services import llm_client
from ..services.llm_client import (
    DEFAULT_GEMINI_MODEL,
    DEFAULT_GROQ_MODEL,
    DEFAULT_TIMEOUT,
    PRICING_URLS,
    LLMClientError,
)
from .chatbot_llm_model import PROVIDERS, RECOMMENDED

PROVIDER_LABELS = dict(PROVIDERS)
# Campos que, al cambiar, obligan a probar la conexión antes de guardar.
CONNECTION_KEYS = ("provider", "api_key", "model")


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Sin config_parameter: Odoo borra el parámetro de un booleano en False y, al no existir, el
    # asistente volvía a leerse como activo. Se guarda siempre como "True" / "False".
    chatbot_active = fields.Boolean(string="Chatbot activo", default=True)
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
        string="ID del modelo",
        config_parameter="chatbot_assistant.model",
        default=DEFAULT_GEMINI_MODEL,
        help="ID técnico del modelo (ej. gemini-2.5-flash).",
    )
    chatbot_llm_model_id = fields.Many2one(
        "chatbot.llm.model",
        string="Modelo",
        domain="[('provider', '=', chatbot_provider), ('available', '=', True)]",
        help="Modelos de texto disponibles del proveedor elegido. Use 'Actualizar modelos' para "
             "traer el listado vigente.",
    )
    chatbot_catalog_count = fields.Integer(compute="_compute_chatbot_catalog")
    chatbot_models_synced = fields.Char(string="Última actualización", compute="_compute_chatbot_catalog")
    chatbot_model_warning = fields.Char(compute="_compute_chatbot_catalog")
    chatbot_pricing_url = fields.Char(compute="_compute_chatbot_catalog")
    chatbot_last_verified = fields.Char(
        string="Última verificación",
        config_parameter="chatbot_assistant.last_verified",
        readonly=True,
    )
    chatbot_llm_status = fields.Char(string="Estado del proveedor", compute="_compute_chatbot_llm_status")
    chatbot_temperature = fields.Float(
        string="Temperature",
        config_parameter="chatbot_assistant.temperature",
        default=0.1,
    )
    chatbot_timeout = fields.Integer(
        string="Timeout (segundos)",
        config_parameter="chatbot_assistant.timeout",
        default=DEFAULT_TIMEOUT,
        help="Tiempo máximo de espera por intento. Si se agota, se reintenta una vez.",
    )

    chatbot_log_retention_days = fields.Integer(
        string="Conservar auditoría (días)",
        config_parameter="chatbot_assistant.log_retention_days",
        default=0,
        help="Los registros de auditoría más antiguos se borran cada día. 0 = conservar todo.",
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        res["chatbot_active"] = llm_client.get_chatbot_config(self.env)["active"]
        provider = res.get("chatbot_provider") or "gemini"
        res["chatbot_llm_model_id"] = self.env["chatbot.llm.model"]._find(provider, res.get("chatbot_model")).id
        return res

    @api.depends("chatbot_provider", "chatbot_model")
    def _compute_chatbot_catalog(self):
        Model = self.env["chatbot.llm.model"]
        ICP = self.env["ir.config_parameter"].sudo()
        for record in self:
            provider = record.chatbot_provider or "gemini"
            record.chatbot_catalog_count = Model.search_count([("provider", "=", provider), ("available", "=", True)])
            record.chatbot_models_synced = ICP.get_param("chatbot_assistant.models_synced_%s" % provider) or _("Nunca")
            record.chatbot_pricing_url = PRICING_URLS.get(provider)
            current = Model._find(provider, record.chatbot_model)
            record.chatbot_model_warning = (
                _("El modelo configurado ya no está disponible en %s. Elige otro.") % PROVIDER_LABELS[provider]
                if current and not current.available else False
            )

    def _compute_chatbot_llm_status(self):
        Log = self.env["chatbot.query.log"].sudo()
        failure = Log.search([("outcome", "in", ("llm_unavailable", "llm_bad_output"))], limit=1)
        success = Log.search([("outcome", "not in", ("llm_unavailable", "llm_bad_output", False))], limit=1)
        if not failure:
            status = _("Sin fallas registradas.")
        else:
            code = dict(Log._fields["error_code"]._description_selection(self.env)).get(failure.error_code, "")
            status = _("Última falla: %(date)s · %(code)s · %(model)s") % {
                "date": self._chatbot_format_datetime(failure.create_date),
                "code": code or _("Otro"),
                "model": failure.llm_model or "-",
            }
            if success and success.create_date > failure.create_date:
                status += _(" (desde entonces respondió bien)")
        for record in self:
            record.chatbot_llm_status = status

    def _chatbot_format_datetime(self, value):
        return fields.Datetime.context_timestamp(self, value).strftime("%Y-%m-%d %H:%M")

    @api.onchange("chatbot_llm_model_id")
    def _onchange_chatbot_llm_model_id(self):
        if self.chatbot_llm_model_id:
            self.chatbot_model = self.chatbot_llm_model_id.model_id

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
            "timeout": self.chatbot_timeout or DEFAULT_TIMEOUT,
        }

    def action_chatbot_sync_models(self):
        """Trae el listado vigente del proveedor elegido y sincroniza el catálogo."""
        self.ensure_one()
        config = self._chatbot_runtime_config()
        try:
            models_data = llm_client.list_models(config)
        except LLMClientError as exc:
            raise UserError(exc.admin_message or exc.message) from exc
        counts = self.env["chatbot.llm.model"].sudo()._sync_provider(config["provider"], models_data)
        message = _(
            "%(provider)s: %(total)s modelos de texto. Nuevos: %(added)s · actualizados: %(updated)s · "
            "reactivados: %(reactivated)s · no disponibles: %(unavailable)s."
        ) % dict(counts, provider=PROVIDER_LABELS[config["provider"]], total=len(models_data))
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Catálogo de modelos actualizado"),
                "message": message,
                "type": "success",
                "sticky": False,
            },
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
        if (result["model"], config["provider"]) == (
            (self.env["ir.config_parameter"].sudo().get_param("chatbot_assistant.model") or "").replace("models/", ""),
            self.env["ir.config_parameter"].sudo().get_param("chatbot_assistant.provider"),
        ):
            self.env["ir.config_parameter"].sudo().set_param(
                "chatbot_assistant.last_verified",
                _("Conexión verificada el %(date)s con %(model)s") % {
                    "date": self._chatbot_format_datetime(fields.Datetime.now()),
                    "model": result["model"],
                },
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
        """Al cambiar de proveedor siempre se usa su modelo recomendado (no se adivina por el nombre)."""
        provider = self.chatbot_provider or "gemini"
        self.chatbot_model = RECOMMENDED[provider]
        self.chatbot_llm_model_id = self.env["chatbot.llm.model"]._find(provider, self.chatbot_model)

    def set_values(self):
        """Si cambió el proveedor, la API key o el modelo, prueba la conexión antes de guardar."""
        for record in self:
            if record.chatbot_llm_model_id:
                record.chatbot_model = record.chatbot_llm_model_id.model_id
            record._chatbot_check_before_save()
        super().set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "chatbot_assistant.active", "True" if self[:1].chatbot_active else "False",
        )

    def _chatbot_check_before_save(self):
        self.ensure_one()
        saved = llm_client.get_chatbot_config(self.env)
        config = self._chatbot_runtime_config()
        if not self.chatbot_active or all(saved[key] == config[key] for key in CONNECTION_KEYS):
            # Desactivar o cambiar solo otros datos no requiere conexión con el proveedor.
            return
        provider_label = PROVIDER_LABELS[config["provider"]]
        Model = self.env["chatbot.llm.model"]
        if not Model._find(config["provider"], config["model"]) and Model.search_count([
            ("provider", "!=", config["provider"]), ("model_id", "=", config["model"]),
        ]):
            raise UserError(_("El modelo '%(model)s' no pertenece a %(provider)s.") % {
                "model": config["model"], "provider": provider_label,
            })
        try:
            result = llm_client.test_connection(config)
        except LLMClientError as exc:
            raise UserError(
                _("No se guardó la configuración: la prueba de conexión falló.\n%s")
                % (exc.admin_message or exc.message)
            ) from exc
        self.chatbot_last_verified = _("Conexión verificada el %(date)s con %(model)s") % {
            "date": self._chatbot_format_datetime(fields.Datetime.now()),
            "model": result["model"],
        }
