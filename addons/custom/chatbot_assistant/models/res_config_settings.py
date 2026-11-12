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
# Errores que indican una configuración que nunca funcionará: impiden guardar aunque el otro modelo responda.
CONFIG_ERROR_CODES = ("auth", "model", "model_not_found", "missing_key", "missing_model")

# El modelo principal y el de respaldo tienen los mismos campos, con distinto prefijo.
SLOTS = {
    "primary": {"field": "chatbot_%s", "param": "chatbot_assistant.%s", "label": ""},
    "fallback": {"field": "chatbot_fallback_%s", "param": "chatbot_assistant.fallback_%s",
                 "label": " del modelo de respaldo"},
}


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Sin config_parameter: Odoo borra el parámetro de un booleano en False y, al no existir, el
    # asistente volvía a leerse como activo. Se guarda siempre como "True" / "False".
    chatbot_active = fields.Boolean(string="Chatbot activo", default=True)
    chatbot_provider = fields.Selection(
        selection=PROVIDERS,
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
    chatbot_catalog_hint = fields.Char(compute="_compute_chatbot_catalog")
    chatbot_pricing_url = fields.Char(compute="_compute_chatbot_catalog")
    chatbot_last_verified = fields.Char(
        string="Última verificación",
        config_parameter="chatbot_assistant.last_verified",
        readonly=True,
    )
    chatbot_llm_status = fields.Char(string="Estado del proveedor", compute="_compute_chatbot_llm_status")

    # Modelo de respaldo: responde cuando el principal no está disponible.
    chatbot_fallback_active = fields.Boolean(string="Usar modelo de respaldo", default=False)
    chatbot_fallback_provider = fields.Selection(
        selection=PROVIDERS,
        string="Proveedor de respaldo",
        config_parameter="chatbot_assistant.fallback_provider",
        default="groq",
    )
    chatbot_fallback_api_key = fields.Char(
        string="API Key de respaldo",
        config_parameter="chatbot_assistant.fallback_api_key",
        groups="base.group_system,chatbot_assistant.group_chatbot_manager",
    )
    chatbot_fallback_model = fields.Char(
        string="ID del modelo de respaldo",
        config_parameter="chatbot_assistant.fallback_model",
        default=DEFAULT_GROQ_MODEL,
    )
    chatbot_fallback_llm_model_id = fields.Many2one(
        "chatbot.llm.model",
        string="Modelo de respaldo",
        domain="[('provider', '=', chatbot_fallback_provider), ('available', '=', True)]",
    )
    chatbot_fallback_catalog_count = fields.Integer(compute="_compute_chatbot_catalog")
    chatbot_fallback_models_synced = fields.Char(string="Última actualización (respaldo)",
                                                 compute="_compute_chatbot_catalog")
    chatbot_fallback_model_warning = fields.Char(compute="_compute_chatbot_catalog")
    chatbot_fallback_catalog_hint = fields.Char(compute="_compute_chatbot_catalog")
    chatbot_fallback_pricing_url = fields.Char(compute="_compute_chatbot_catalog")
    chatbot_fallback_last_verified = fields.Char(
        string="Última verificación (respaldo)",
        config_parameter="chatbot_assistant.fallback_last_verified",
        readonly=True,
    )
    chatbot_fallback_status = fields.Char(string="Uso del respaldo", compute="_compute_chatbot_llm_status")

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

    # ------------------------------------------------------------------ utilidades por modelo
    def _chatbot_get(self, slot, name):
        return self[SLOTS[slot]["field"] % name]

    def _chatbot_set(self, slot, name, value):
        self[SLOTS[slot]["field"] % name] = value

    def _chatbot_saved(self, slot, resolve_key=False):
        """Configuración guardada del modelo (sin reutilizar la key del principal, salvo resolve_key)."""
        if slot == "primary":
            return llm_client.get_chatbot_config(self.env)
        return llm_client.get_fallback_config(self.env, resolve_key=resolve_key)

    @api.model
    def get_values(self):
        res = super().get_values()
        res["chatbot_active"] = llm_client.get_chatbot_config(self.env)["active"]
        res["chatbot_fallback_active"] = llm_client.get_fallback_config(self.env)["active"]
        Model = self.env["chatbot.llm.model"]
        res["chatbot_llm_model_id"] = Model._find(
            res.get("chatbot_provider") or "gemini", res.get("chatbot_model")).id
        res["chatbot_fallback_llm_model_id"] = Model._find(
            res.get("chatbot_fallback_provider") or "groq", res.get("chatbot_fallback_model")).id
        return res

    @api.depends("chatbot_provider", "chatbot_model", "chatbot_fallback_provider", "chatbot_fallback_model")
    def _compute_chatbot_catalog(self):
        Model = self.env["chatbot.llm.model"]
        ICP = self.env["ir.config_parameter"].sudo()
        for record in self:
            for slot in SLOTS:
                provider = record._chatbot_get(slot, "provider") or ("gemini" if slot == "primary" else "groq")
                count = Model.search_count([("provider", "=", provider), ("available", "=", True)])
                record._chatbot_set(slot, "catalog_count", count)
                record._chatbot_set(slot, "models_synced",
                                    ICP.get_param("chatbot_assistant.models_synced_%s" % provider) or _("Nunca"))
                record._chatbot_set(slot, "pricing_url", PRICING_URLS.get(provider))
                current = Model._find(provider, record._chatbot_get(slot, "model"))
                record._chatbot_set(slot, "model_warning", (
                    _("El modelo configurado ya no está disponible en %s. Elige otro.") % PROVIDER_LABELS[provider]
                    if current and not current.available else False
                ))
                # Tras instalar solo hay 1 modelo semilla por proveedor; hace falta sincronizar.
                record._chatbot_set(slot, "catalog_hint", _(
                    "Solo hay %(count)s modelo(s) de %(provider)s en el catálogo. "
                    "Pegue la API Key de %(provider)s y pulse «Actualizar modelos» "
                    "(no hace falta Guardar antes)."
                ) % {"count": count, "provider": PROVIDER_LABELS[provider]} if count <= 1 else False)

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
        used = Log.search([("fallback_used", "=", True)], limit=1)
        if used:
            week = fields.Datetime.subtract(fields.Datetime.now(), days=7)
            fallback_status = _("Respondió %(count)s consulta(s) en los últimos 7 días; la última el %(date)s.") % {
                "count": Log.search_count([("fallback_used", "=", True), ("create_date", ">=", week)]),
                "date": self._chatbot_format_datetime(used.create_date),
            }
        else:
            fallback_status = _("Todavía no ha tenido que responder.")
        for record in self:
            record.chatbot_llm_status = status
            record.chatbot_fallback_status = fallback_status

    def _chatbot_format_datetime(self, value):
        return fields.Datetime.context_timestamp(self, value).strftime("%Y-%m-%d %H:%M")

    @api.onchange("chatbot_llm_model_id")
    def _onchange_chatbot_llm_model_id(self):
        if self.chatbot_llm_model_id:
            self.chatbot_model = self.chatbot_llm_model_id.model_id

    @api.onchange("chatbot_fallback_llm_model_id")
    def _onchange_chatbot_fallback_llm_model_id(self):
        if self.chatbot_fallback_llm_model_id:
            self.chatbot_fallback_model = self.chatbot_fallback_llm_model_id.model_id

    # ------------------------------------------------------------------ configuración en uso
    def _chatbot_runtime_config(self, check_format=True, slot="primary"):
        """Config desde el formulario; si la key viene vacía, usa la guardada solo si el proveedor coincide."""
        self.ensure_one()
        default_provider = "gemini" if slot == "primary" else "groq"
        provider = self._chatbot_get(slot, "provider") or default_provider
        api_key = (self._chatbot_get(slot, "api_key") or "").strip()
        if not api_key:
            # En Ajustes, los campos password a menudo llegan vacíos si no se vuelven a pegar.
            # Solo reutilizar la key guardada cuando el proveedor del formulario es el mismo.
            saved = self._chatbot_saved(slot)
            if saved["provider"] == provider:
                api_key = (saved["api_key"] or "").strip()
        if not api_key and slot == "fallback" and provider == (self.chatbot_provider or "gemini"):
            # Respaldo del mismo proveedor sin key propia: usa la del modelo principal.
            api_key = self._chatbot_runtime_config(check_format=False)["api_key"]
        if check_format:
            self._chatbot_check_api_key_format(provider, api_key)
        default_model = DEFAULT_GEMINI_MODEL if provider == "gemini" else DEFAULT_GROQ_MODEL
        model = (self._chatbot_get(slot, "model") or default_model).strip()
        selected = self._chatbot_get(slot, "llm_model_id")
        if selected and selected.provider == provider:
            # El desplegable manda: el campo de texto solo se sincroniza con el onchange del formulario.
            model = selected.model_id
        return {
            "provider": provider,
            "api_key": api_key,
            "model": model,
            "temperature": self.chatbot_temperature if self.chatbot_temperature is not None else 0.1,
            "timeout": self.chatbot_timeout or DEFAULT_TIMEOUT,
        }

    def _chatbot_check_api_key_format(self, provider, api_key):
        """Avisa si la key parece del proveedor equivocado (Gemini vs Groq)."""
        if not api_key:
            return
        key = api_key.strip()
        if provider == "groq" and key.startswith("AIza"):
            raise UserError(_(
                "Esa API Key parece de Google Gemini (empieza por AIza), pero el proveedor "
                "elegido es Groq.\n\n"
                "1. En console.groq.com cree una clave (empieza por gsk_).\n"
                "2. Péguela de nuevo en el campo API Key.\n"
                "3. Pulse «Probar conexión» o «Actualizar modelos»."
            ))
        if provider == "gemini" and key.startswith("gsk_"):
            raise UserError(_(
                "Esa API Key parece de Groq (empieza por gsk_), pero el proveedor "
                "elegido es Google Gemini.\n\n"
                "Use una clave de Google AI Studio o cambie el proveedor a Groq."
            ))
        if provider == "groq" and not key.startswith("gsk_"):
            raise UserError(_(
                "La API Key de Groq suele empezar por gsk_. "
                "Vuelva a pegarla completa (sin espacios) y pruebe de nuevo.\n"
                "Si acaba de cambiar de Gemini a Groq, el campo a veces no envía la clave "
                "antigua: hay que pegar la de Groq otra vez."
            ))

    # ------------------------------------------------------------------ botones
    def _chatbot_sync_models(self, slot):
        """Trae el listado vigente del proveedor elegido y sincroniza el catálogo."""
        self.ensure_one()
        config = self._chatbot_runtime_config(slot=slot)
        if not config.get("api_key"):
            raise UserError(_(
                "Pegue la API Key del proveedor elegido antes de actualizar modelos."
            ))
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

    def _chatbot_test_connection(self, slot):
        self.ensure_one()
        config = self._chatbot_runtime_config(slot=slot)
        if not config.get("api_key"):
            raise UserError(_(
                "Pegue la API Key del proveedor elegido antes de probar la conexión."
            ))
        try:
            result = llm_client.test_connection(config)
        except LLMClientError as exc:
            raise UserError(exc.admin_message or exc.message) from exc

        # Solo se actualiza el formulario: la configuración del chat cambia al pulsar Guardar.
        self._chatbot_set(slot, "last_verified", _("Conexión verificada el %(date)s con %(model)s") % {
            "date": self._chatbot_format_datetime(fields.Datetime.now()),
            "model": result["model"],
        })
        info = _(
            "✓ Conexión exitosa · %(provider)s · %(model)s · %(latency)s ms"
        ) % {
            "provider": result["provider"],
            "model": result["model"],
            "latency": result["latency_ms"],
        }
        self.env["ir.config_parameter"].sudo().set_param(
            SLOTS[slot]["param"] % "last_test_info",
            info,
        )
        # Notificación (sin wizard): evita que Ajustes dispare "Unsaved changes" / recarga.
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Prueba de conexión%s") % SLOTS[slot]["label"],
                "message": info,
                "type": "success",
                "sticky": False,
            },
        }

    def action_chatbot_sync_models(self):
        return self._chatbot_sync_models("primary")

    def action_chatbot_test_connection(self):
        return self._chatbot_test_connection("primary")

    def action_chatbot_fallback_sync_models(self):
        return self._chatbot_sync_models("fallback")

    def action_chatbot_fallback_test_connection(self):
        return self._chatbot_test_connection("fallback")

    # ------------------------------------------------------------------ cambio de proveedor
    def _chatbot_apply_provider_change(self, slot):
        """
        Al cambiar a otro proveedor: modelo recomendado y API Key vacía (cada proveedor tiene la suya).
        Si el proveedor es el guardado (al abrir Ajustes, Odoo ejecuta este onchange, o al volver al
        proveedor original), se muestra la configuración guardada en lugar de reemplazarla.
        """
        provider = self._chatbot_get(slot, "provider") or ("gemini" if slot == "primary" else "groq")
        saved = self._chatbot_saved(slot)
        Model = self.env["chatbot.llm.model"]
        if provider == saved["provider"]:
            self._chatbot_set(slot, "model", saved["model"])
            self._chatbot_set(slot, "llm_model_id", Model._find(provider, saved["model"]))
            self._chatbot_set(slot, "api_key", saved["api_key"] or False)
            return
        self._chatbot_set(slot, "model", RECOMMENDED[provider])
        self._chatbot_set(slot, "llm_model_id", Model._find(provider, RECOMMENDED[provider]))
        # Evita reutilizar la key del proveedor anterior (password a menudo no se reenvía bien).
        self._chatbot_set(slot, "api_key", False)
        self._chatbot_set(slot, "last_verified", False)

    @api.onchange("chatbot_provider")
    def _onchange_chatbot_provider(self):
        self._chatbot_apply_provider_change("primary")

    @api.onchange("chatbot_fallback_provider")
    def _onchange_chatbot_fallback_provider(self):
        self._chatbot_apply_provider_change("fallback")

    # ------------------------------------------------------------------ guardar
    def set_values(self):
        """
        Si cambió el proveedor, la API key o el modelo (del principal o del respaldo), prueba la
        conexión antes de guardar. Basta con que responda uno de los dos modelos: un fallo pasajero
        (tiempo agotado, servicio caído, cuota agotada) no impide guardar si el otro funciona, pero un
        error de configuración (clave inválida, modelo inexistente) siempre lo impide.
        """
        for record in self:
            for slot in SLOTS:
                saved = record._chatbot_saved(slot)
                provider = record._chatbot_get(slot, "provider") or ("gemini" if slot == "primary" else "groq")
                if not (record._chatbot_get(slot, "api_key") or "").strip() and provider == saved["provider"]:
                    # El campo llega vacío si se cambió de proveedor y se volvió al original sin pegar la
                    # clave: se conserva la guardada en lugar de borrarla.
                    record._chatbot_set(slot, "api_key", saved["api_key"] or False)
                selected = record._chatbot_get(slot, "llm_model_id")
                if selected:
                    record._chatbot_set(slot, "model", selected.model_id)
            record._chatbot_check_connections()
        super().set_values()
        icp = self.env["ir.config_parameter"].sudo()
        icp.set_param("chatbot_assistant.active", "True" if self[:1].chatbot_active else "False")
        icp.set_param("chatbot_assistant.fallback_active", "True" if self[:1].chatbot_fallback_active else "False")

    def _chatbot_slot_enabled(self, slot):
        if slot == "primary":
            return self.chatbot_active
        # Con el asistente apagado no se prueba nada, tampoco el respaldo.
        return self.chatbot_active and self.chatbot_fallback_active

    def _chatbot_check_connections(self):
        self.ensure_one()
        pending = {}
        for slot in SLOTS:
            config = self._chatbot_prepare_check(slot)
            if config:
                pending[slot] = config
        results = {slot: self._chatbot_try_connection(slot, config) for slot, config in pending.items()}
        failed = [slot for slot, result in results.items() if result is not True]
        if not failed:
            return
        # Un modelo cambiado no respondió por un fallo pasajero: se comprueba si el otro funciona.
        for slot in SLOTS:
            if slot not in results and self._chatbot_slot_enabled(slot):
                config = self._chatbot_runtime_config(check_format=False, slot=slot)
                results[slot] = self._chatbot_try_connection(slot, config, raise_config=False, mark=False)
        exc = results[failed[0]]
        if not any(result is True for result in results.values()):
            raise UserError(_(
                "No se guardó la configuración: ningún modelo respondió a la prueba de conexión.\n%s"
            ) % (exc.admin_message or exc.message))
        for slot in failed:
            self._chatbot_set(slot, "last_verified", _(
                "No se pudo verificar el %(date)s (%(detail)s). Se guardó porque el otro modelo respondió."
            ) % {"date": self._chatbot_format_datetime(fields.Datetime.now()),
                 "detail": results[slot].admin_message or results[slot].message})

    def _chatbot_prepare_check(self, slot):
        """Valida el modelo y retorna su configuración si hay que probar la conexión (None si no)."""
        enabled = self._chatbot_slot_enabled(slot)
        newly_enabled = slot == "fallback" and enabled and not llm_client.get_fallback_config(self.env)["active"]
        saved = self._chatbot_saved(slot, resolve_key=True)
        config = self._chatbot_runtime_config(check_format=False, slot=slot)
        if not enabled or (not newly_enabled and all(saved[key] == config[key] for key in CONNECTION_KEYS)):
            # Desactivar o cambiar solo otros datos no requiere conexión con el proveedor
            # (ni revisar el formato de la API key).
            return None
        label = SLOTS[slot]["label"]
        if slot == "fallback":
            primary = self._chatbot_runtime_config(check_format=False)
            if (primary["provider"], primary["model"]) == (config["provider"], config["model"]):
                raise UserError(_(
                    "El modelo de respaldo es el mismo que el principal (%s). Elija otro modelo o, mejor, "
                    "otro proveedor, para que una caída del principal no afecte también al respaldo."
                ) % config["model"])
        self._chatbot_check_api_key_format(config["provider"], config["api_key"])
        provider_label = PROVIDER_LABELS[config["provider"]]
        Model = self.env["chatbot.llm.model"]
        if not Model._find(config["provider"], config["model"]) and Model.search_count([
            ("provider", "!=", config["provider"]), ("model_id", "=", config["model"]),
        ]):
            raise UserError(_("El modelo '%(model)s' no pertenece a %(provider)s.") % {
                "model": config["model"], "provider": provider_label,
            })
        if not config["api_key"]:
            raise UserError(_("No se guardó la configuración: falta la API Key%s.") % label)
        return config

    def _chatbot_try_connection(self, slot, config, raise_config=True, mark=True):
        """
        Prueba la conexión. Retorna True si responde y el error si es un fallo pasajero.
        Un error de configuración (clave inválida, modelo inexistente) impide guardar.
        """
        try:
            result = llm_client.test_connection(config)
        except LLMClientError as exc:
            if raise_config and exc.code in CONFIG_ERROR_CODES:
                raise UserError(
                    _("No se guardó la configuración: la prueba de conexión%(label)s falló.\n%(detail)s") % {
                        "label": SLOTS[slot]["label"], "detail": exc.admin_message or exc.message,
                    }
                ) from exc
            return exc
        if mark:
            self._chatbot_set(slot, "last_verified", _("Conexión verificada el %(date)s con %(model)s") % {
                "date": self._chatbot_format_datetime(fields.Datetime.now()),
                "model": result["model"],
            })
        return True
