# -*- coding: utf-8 -*-
import json

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ChatbotSession(models.Model):
    _name = "chatbot.session"
    _description = "Sesión del asistente conversacional"
    _order = "write_date desc, id desc"

    name = fields.Char(required=True, default=lambda self: _("Nueva consulta"))
    user_id = fields.Many2one(
        "res.users",
        string="Usuario",
        required=True,
        default=lambda self: self.env.user,
        index=True,
    )
    state = fields.Selection(
        selection=[
            ("open", "Abierta"),
            ("closed", "Cerrada"),
        ],
        default="open",
        required=True,
    )
    message_ids = fields.One2many("chatbot.message", "session_id", string="Mensajes")
    message_input = fields.Text(string="Escriba su consulta")
    discuss_channel_id = fields.Many2one(
        "discuss.channel",
        string="Canal Discuss",
        ondelete="set null",
        index=True,
        help="Canal DM usado cuando el asistente opera dentro de Discuss.",
    )
    pending_intent = fields.Char()
    pending_entities_json = fields.Text(default="{}")
    last_intent = fields.Char(readonly=True)
    last_status = fields.Char(readonly=True)

    def action_send_message(self):
        self.ensure_one()
        text = (self.message_input or "").strip()
        if not text:
            raise UserError(_("Escriba una consulta antes de enviar."))
        if self.state != "open":
            raise UserError(_("Esta sesión está cerrada. Abra una nueva."))

        self.env["chatbot.message"].create({
            "session_id": self.id,
            "role": "user",
            "body": text,
        })
        self.message_input = False

        result = self.env["chatbot.orchestrator"].process_message(self, text)
        self.env["chatbot.message"].create({
            "session_id": self.id,
            "role": "assistant",
            "body": result.get("reply") or _("Sin respuesta"),
            "intent": result.get("intent"),
            "status": result.get("status"),
        })
        self.last_intent = result.get("intent")
        self.last_status = result.get("status")

        # Actualizar título de sesión con un resumen corto
        if self.name == _("Nueva consulta") or self.name.startswith("Nueva"):
            self.name = text[:60] + ("…" if len(text) > 60 else "")

        return {
            "type": "ir.actions.act_window",
            "res_model": "chatbot.session",
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_close(self):
        self.write({
            "state": "closed",
            "pending_intent": False,
            "pending_entities_json": "{}",
        })
        return True

    def get_pending_entities(self):
        self.ensure_one()
        try:
            return json.loads(self.pending_entities_json or "{}")
        except json.JSONDecodeError:
            return {}

    def set_pending(self, intent, entities):
        self.ensure_one()
        self.pending_intent = intent or False
        self.pending_entities_json = json.dumps(entities or {}, ensure_ascii=False)

    def clear_pending(self):
        self.ensure_one()
        self.pending_intent = False
        self.pending_entities_json = "{}"

    def get_short_context(self, max_turns=3):
        """Memoria corta: últimos turnos + pending."""
        self.ensure_one()
        messages = self.message_ids.sorted("id")[-max_turns * 2 :]
        history = [
            {"role": m.role, "body": m.body[:300]}
            for m in messages
        ]
        return {
            "pending_intent": self.pending_intent or None,
            "pending_entities": self.get_pending_entities(),
            "recent_messages": history,
        }

    @api.model
    def action_open_new_session(self):
        """Compatibilidad: abre el chat Discuss (UX principal)."""
        return self.env["chatbot.discuss.service"].open_assistant_chat()

    @api.model
    def action_open_form_session(self):
        """Sesión formulario (respaldo / auditoría manual)."""
        session = self.create({})
        return {
            "type": "ir.actions.act_window",
            "name": _("Asistente conversacional (formulario)"),
            "res_model": "chatbot.session",
            "res_id": session.id,
            "view_mode": "form",
            "target": "current",
        }
