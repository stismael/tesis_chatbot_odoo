# -*- coding: utf-8 -*-
from odoo import models


class MailBot(models.AbstractModel):
    _inherit = "mail.bot"

    def _apply_logic(self, record, values, command=None):
        # No interferir en el DM del Asistente ERP
        if record._name == "discuss.channel":
            bot = self.env.ref("chatbot_assistant.partner_chatbot_assistant", raise_if_not_found=False)
            if bot and bot in record.with_context(active_test=False).channel_partner_ids:
                return
        return super()._apply_logic(record, values, command=command)
