# -*- coding: utf-8 -*-
"""Servicio Discuss: responde en DM como OdooBot, usando el orquestador."""
import logging
import re

from markupsafe import Markup
from odoo import api, models, _
from odoo.tools import html2plaintext, html_escape

from ..services.help_text import build_welcome_markup
from ..services.llm_client import USER_MESSAGES

_logger = logging.getLogger(__name__)

BOT_XMLID = "chatbot_assistant.partner_chatbot_assistant"
WELCOME_BODY = build_welcome_markup()


class ChatbotDiscussService(models.AbstractModel):
    _name = "chatbot.discuss.service"
    _description = "Asistente ERP en Discuss"

    @api.model
    def _bot_partner(self):
        return self.env.ref(BOT_XMLID, raise_if_not_found=False)

    @api.model
    def is_assistant_channel(self, channel):
        bot = self._bot_partner()
        if not bot or channel._name != "discuss.channel":
            return False
        if channel.channel_type != "chat":
            return False
        partners = channel.with_context(active_test=False).channel_partner_ids
        return bot in partners

    @api.model
    def _normalize_body(self, body):
        if not body:
            return ""
        text = html2plaintext(str(body) or "")
        text = text.replace("\xa0", " ").strip()
        text = re.sub(r"\s+", " ", text)
        return text

    @api.model
    def _format_reply_html(self, reply):
        safe = html_escape(reply or "")
        return Markup("<p>%s</p>") % Markup("<br/>").join(Markup(line) for line in safe.split("\n"))

    @api.model
    def _is_bot_author(self, author_id):
        if not author_id:
            return False
        bot = self._bot_partner()
        if bot and author_id == bot.id:
            return True
        odoobot = self.env.ref("base.partner_root", raise_if_not_found=False)
        if odoobot and author_id == odoobot.id:
            return True
        author = self.env["res.partner"].browse(author_id)
        return bool(author) and author.im_status == "bot"

    @api.model
    def apply_logic(self, channel, msg_vals):
        """Responde si el mensaje es un comentario de usuario en el DM del asistente."""
        if self.env.context.get("chatbot_assistant_reply"):
            return

        channel.ensure_one()
        bot = self._bot_partner()
        if not bot:
            return
        if not self.is_assistant_channel(channel):
            return

        author_id = msg_vals.get("author_id")
        if self._is_bot_author(author_id):
            return
        if msg_vals.get("message_type") and msg_vals.get("message_type") != "comment":
            return

        body = self._normalize_body(msg_vals.get("body"))
        if not body or body.startswith("/"):
            return

        session = self._get_or_create_session(channel)
        log_id = False
        try:
            self.env["chatbot.message"].create({
                "session_id": session.id,
                "role": "user",
                "body": body,
            })
            result = self.env["chatbot.orchestrator"].process_message(session, body)
            log_id = result.get("log_id")
            reply = result.get("reply") or _("Sin respuesta")
            self.env["chatbot.message"].create({
                "session_id": session.id,
                "role": "assistant",
                "body": reply,
                "intent": result.get("intent"),
                "status": result.get("status"),
            })
            new_name = session.name
            if not new_name or new_name in (_("Nueva consulta"), _("Discuss")):
                new_name = body[:60] + ("…" if len(body) > 60 else "")
            session.write({
                "last_intent": result.get("intent"),
                "last_status": result.get("status"),
                "name": new_name,
            })
        except Exception:
            _logger.exception("Error en Asistente ERP (Discuss)")
            reply = USER_MESSAGES["generic"]

        reply_message = channel.with_context(chatbot_assistant_reply=True).sudo().message_post(
            author_id=bot.id,
            body=self._format_reply_html(reply),
            message_type="comment",
            subtype_xmlid="mail.mt_comment",
            silent=True,
        )
        if log_id:
            # Liga la respuesta al log para registrar la valoración 👍/👎 del usuario.
            self.env["chatbot.query.log"].sudo().browse(log_id).reply_message_id = reply_message.id

    @api.model
    def _get_or_create_session(self, channel):
        Session = self.env["chatbot.session"]
        session = Session.search([
            ("discuss_channel_id", "=", channel.id),
            ("user_id", "=", self.env.user.id),
            ("state", "=", "open"),
        ], limit=1)
        if session:
            return session
        return Session.create({
            "name": _("Discuss"),
            "user_id": self.env.user.id,
            "discuss_channel_id": channel.id,
        })

    @api.model
    def open_assistant_chat(self):
        """Abre (o crea) el DM con el Asistente ERP y muestra Discuss."""
        bot = self._bot_partner()
        if not bot:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Asistente ERP"),
                    "message": _("No se encontró el contacto del asistente. Actualice el módulo."),
                    "type": "danger",
                    "sticky": False,
                },
            }

        channel = self.env["discuss.channel"].channel_get(
            [bot.id],
            pin=True,
            force_open=True,
        )
        messages = channel.message_ids.filtered(lambda m: m.message_type == "comment")
        if not messages:
            channel.with_context(chatbot_assistant_reply=True).sudo().message_post(
                author_id=bot.id,
                body=WELCOME_BODY,
                message_type="comment",
                subtype_xmlid="mail.mt_comment",
                silent=True,
            )
            self._get_or_create_session(channel)

        return {
            "type": "ir.actions.act_url",
            "url": f"/odoo/action-mail.action_discuss?active_id={channel.id}",
            "target": "self",
        }
