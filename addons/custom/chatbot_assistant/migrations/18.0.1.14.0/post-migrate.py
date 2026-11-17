# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Google dejó de ofrecer gemini-2.5-flash a cuentas nuevas: la configuración pasa al modelo recomendado actual."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["chatbot.llm.model"]._replace_retired_models()
