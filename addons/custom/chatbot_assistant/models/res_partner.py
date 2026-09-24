# -*- coding: utf-8 -*-
from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.depends_context("uid")
    def _compute_im_status(self):
        super()._compute_im_status()
        bot = self.env.ref("chatbot_assistant.partner_chatbot_assistant", raise_if_not_found=False)
        if bot and bot in self:
            bot.im_status = "bot"
