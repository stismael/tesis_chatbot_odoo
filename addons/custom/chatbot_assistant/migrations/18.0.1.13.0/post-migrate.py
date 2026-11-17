# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Groq retiró llama-3.3-70b-versatile: la configuración guardada pasa al modelo recomendado actual."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["chatbot.llm.model"]._replace_retired_groq_models()
