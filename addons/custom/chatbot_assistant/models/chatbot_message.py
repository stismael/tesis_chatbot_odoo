# -*- coding: utf-8 -*-
from odoo import fields, models


class ChatbotMessage(models.Model):
    _name = "chatbot.message"
    _description = "Mensaje del asistente conversacional"
    _order = "id asc"

    session_id = fields.Many2one(
        "chatbot.session",
        required=True,
        ondelete="cascade",
        index=True,
    )
    role = fields.Selection(
        selection=[
            ("user", "Usuario"),
            ("assistant", "Asistente"),
            ("system", "Sistema"),
        ],
        required=True,
        default="user",
    )
    body = fields.Text(required=True)
    intent = fields.Char()
    status = fields.Char()
