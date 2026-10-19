# -*- coding: utf-8 -*-
from odoo import api, models


class MailMessageReaction(models.Model):
    _inherit = "mail.message.reaction"

    @api.model_create_multi
    def create(self, vals_list):
        reactions = super().create(vals_list)
        self.env["chatbot.query.log"]._update_feedback_from_messages(reactions.message_id)
        return reactions

    def unlink(self):
        messages = self.message_id
        res = super().unlink()
        self.env["chatbot.query.log"]._update_feedback_from_messages(messages)
        return res
