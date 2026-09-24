# -*- coding: utf-8 -*-
from odoo import fields, models


class ChatbotQueryLog(models.Model):
    _name = "chatbot.query.log"
    _description = "Auditoría de consultas del chatbot"
    _order = "create_date desc, id desc"

    name = fields.Char(string="Resumen", required=True)
    user_id = fields.Many2one("res.users", required=True, index=True)
    session_id = fields.Many2one("chatbot.session", ondelete="set null", index=True)
    query = fields.Text(required=True)
    intent = fields.Char(index=True)
    status = fields.Char(index=True)
    llm_json = fields.Text()
    reply = fields.Text()
    success = fields.Boolean(default=False)
    latency_ms = fields.Integer()
    error = fields.Char()
    handler_data_json = fields.Text()
