# -*- coding: utf-8 -*-
from markupsafe import Markup

from odoo import fields, models, _


class ResUsers(models.Model):
    _inherit = "res.users"

    chatbot_assistant_initialized = fields.Boolean(
        string="Asistente ERP inicializado",
        default=False,
        copy=False,
    )

    def _on_webclient_bootstrap(self):
        """Al entrar a Odoo, deja el DM del Asistente ERP listo en Discuss (como OdooBot)."""
        super()._on_webclient_bootstrap()
        if self._is_internal() and not self.chatbot_assistant_initialized:
            self._init_chatbot_assistant()

    def _init_chatbot_assistant(self):
        self.ensure_one()
        bot = self.env.ref(
            "chatbot_assistant.partner_chatbot_assistant",
            raise_if_not_found=False,
        )
        if not bot:
            return

        channel = self.env["discuss.channel"].with_user(self).channel_get(
            [bot.id],
            pin=True,
        )
        comments = channel.message_ids.filtered(lambda m: m.message_type == "comment")
        if not comments:
            welcome = Markup(
                "<p>Hola, soy el <b>Asistente ERP</b>.</p>"
                "<p>Puedo consultar en solo lectura: facturas, inventario, "
                "ventas por cliente y vendedor asignado.</p>"
                "<p>Escribe tu pregunta aquí mismo, por ejemplo:<br/>"
                "<i>¿Quién es el vendedor de Comercial Andina S.A.?</i></p>"
            )
            channel.with_context(chatbot_assistant_reply=True).sudo().message_post(
                author_id=bot.id,
                body=welcome,
                message_type="comment",
                silent=True,
                subtype_xmlid="mail.mt_comment",
            )

        # Sesión interna enlazada al canal
        Session = self.env["chatbot.session"].sudo()
        session = Session.search([
            ("discuss_channel_id", "=", channel.id),
            ("user_id", "=", self.id),
            ("state", "=", "open"),
        ], limit=1)
        if not session:
            Session.create({
                "name": _("Discuss"),
                "user_id": self.id,
                "discuss_channel_id": channel.id,
            })

        self.sudo().chatbot_assistant_initialized = True
        return channel
