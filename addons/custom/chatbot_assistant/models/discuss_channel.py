# -*- coding: utf-8 -*-
from odoo import models


class DiscussChannel(models.Model):
    _inherit = "discuss.channel"

    def _message_post_after_hook(self, message, msg_vals):
        """Dispara el Asistente ERP en DMs (después de OdooBot, con anti-reentrada)."""
        res = super()._message_post_after_hook(message, msg_vals)
        if not self.env.context.get("chatbot_assistant_reply"):
            self.env["chatbot.discuss.service"].apply_logic(self, msg_vals)
        return res

    def _channel_basic_info(self):
        info = super()._channel_basic_info()
        info["isChatbotAssistant"] = self.env["chatbot.discuss.service"].is_assistant_channel(self)
        return info

    def execute_command_help(self, **kwargs):
        self.ensure_one()
        if self.env["chatbot.discuss.service"].is_assistant_channel(self):
            from ..services.help_text import build_help_markup
            bot = self.env.ref(
                "chatbot_assistant.partner_chatbot_assistant",
                raise_if_not_found=False,
            )
            if bot:
                self.with_context(chatbot_assistant_reply=True).sudo().message_post(
                    author_id=bot.id,
                    body=build_help_markup(
                        self.env["chatbot.intent.permission"]._allowed_intents()
                    ),
                    message_type="comment",
                    subtype_xmlid="mail.mt_comment",
                    silent=True,
                )
            return
        return super().execute_command_help(**kwargs)
