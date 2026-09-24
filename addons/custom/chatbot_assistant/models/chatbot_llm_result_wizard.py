# -*- coding: utf-8 -*-
from odoo import fields, models, _


class ChatbotLlmResultWizard(models.TransientModel):
    _name = "chatbot.llm.result.wizard"
    _description = "Resultado LLM (modelos / prueba de conexión)"

    title = fields.Char(readonly=True)
    body = fields.Text(readonly=True)
    suggested_model = fields.Char(readonly=True)
    apply_suggested = fields.Boolean(
        string="Usar el modelo sugerido en Ajustes",
        default=True,
    )

    def action_close(self):
        return {"type": "ir.actions.act_window_close"}

    def action_apply_suggested(self):
        self.ensure_one()
        if self.suggested_model:
            self.env["ir.config_parameter"].sudo().set_param(
                "chatbot_assistant.model",
                self.suggested_model,
            )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Modelo actualizado"),
                "message": _("Modelo guardado: %s. Vuelva a abrir Ajustes o pulse Guardar tras recargar.")
                % (self.suggested_model or ""),
                "type": "success",
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
