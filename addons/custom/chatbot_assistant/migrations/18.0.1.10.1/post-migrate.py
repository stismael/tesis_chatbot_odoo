# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Rellenar pricing_hint en el catálogo ya sincronizado."""
    from odoo import api, SUPERUSER_ID

    env = api.Environment(cr, SUPERUSER_ID, {})
    Model = env["chatbot.llm.model"].sudo()
    from odoo.addons.chatbot_assistant.services import llm_client

    for record in Model.search([]):
        hint = llm_client.pricing_hint(record.provider, record.model_id)
        if record.pricing_hint != hint:
            record.pricing_hint = hint
