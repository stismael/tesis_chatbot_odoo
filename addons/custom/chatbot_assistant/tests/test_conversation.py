# -*- coding: utf-8 -*-
from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import new_test_user

from ..models.orchestrator import CONVERSATION_FALLBACK, OUT_OF_SCOPE_MSG
from ..services.validator import REPLY_MAX_CHARS
from .common import ChatbotCase
from .test_metrics import fake_llm
from .test_orchestrator_security import COMPLETE_JSON, llm_output


def conversation(reply, intent="conversacion"):
    output = llm_output(intent, "ready" if intent == "conversacion" else "rejected")
    output["reply"] = reply
    return output


@tagged("post_install", "-at_install", "chatbot_assistant")
class TestConversation(ChatbotCase):

    def setUp(self):
        super().setUp()
        self.env["ir.config_parameter"].sudo().set_param("chatbot_assistant.api_key", "clave-de-prueba")
        self.user_env = self.env(user=self.tester)
        self.session = self.user_env["chatbot.session"].create({"name": "conversacion"})

    def _ask(self, text, output, user_env=None):
        user_env = user_env or self.user_env
        session = self.session if user_env is self.user_env else user_env["chatbot.session"].create({"name": "x"})
        with patch(COMPLETE_JSON, side_effect=fake_llm(output)):
            result = user_env["chatbot.orchestrator"].evaluate_query(text, session=session)
        return result, self.env["chatbot.query.log"].browse(result["log_id"])

    def test_saludo_redactado_por_la_ia(self):
        text = "¡Hola! Soy el Asistente ERP, ¿qué necesitas consultar?"
        result, log = self._ask("Hola", conversation(text))
        self.assertEqual(result["reply"], text)
        self.assertEqual((result["intent"], log.outcome), ("conversacion", "conversation"))
        self.assertFalse(result["data"], "La conversación no consulta Odoo")
        self.assertTrue(log.success)

    def test_agradecimiento_no_borra_la_consulta_pendiente(self):
        self._ask("¿cuánto stock hay?", llm_output("consultar_stock", "missing_information", ["product_name"]))
        self.assertEqual(self.session.pending_intent, "consultar_stock")
        result, _log = self._ask("gracias", conversation("¡Con gusto!"))
        self.assertEqual(result["reply"], "¡Con gusto!")
        self.assertEqual(self.session.pending_intent, "consultar_stock")

    def test_pregunta_de_capacidades(self):
        text = "Puedo consultar facturas, inventario, ventas y el vendedor asignado a un cliente."
        result, _log = self._ask("¿Qué puedes hacer?", conversation(text))
        self.assertEqual(result["reply"], text)

    def test_sin_reply_usa_el_respaldo(self):
        result, _log = self._ask("Hola", conversation(None))
        self.assertEqual(result["reply"], CONVERSATION_FALLBACK)

    def test_rechazo_redactado_por_la_ia(self):
        text = "No puedo crear facturas porque solo consulto información. Sí puedo decirte su estado."
        result, log = self._ask("Crea una factura", conversation(text, "fuera_de_alcance"))
        self.assertEqual(result["reply"], text)
        self.assertEqual(log.outcome, "rejected")
        result, _log = self._ask("Crea una factura", conversation(None, "fuera_de_alcance"))
        self.assertEqual(result["reply"], OUT_OF_SCOPE_MSG)

    def test_datos_inventados_se_descartan(self):
        # Si la IA respondiera una pregunta de datos como charla, la cifra nunca llega al usuario.
        result, log = self._ask("¿Cuánto vendí ayer?", conversation("Ayer vendiste 1.250 dólares."))
        self.assertEqual(result["reply"], CONVERSATION_FALLBACK)
        self.assertEqual((log.outcome, log.error_code), ("conversation", "reply_discarded"))
        self.assertNotIn("1.250", log.reply)

        result, log = self._ask("Borra la factura", conversation("No puedo borrar la INV/2026/00001.", "fuera_de_alcance"))
        self.assertEqual(result["reply"], OUT_OF_SCOPE_MSG)
        self.assertEqual(log.error_code, "reply_discarded")

    def test_respuesta_larga_se_acorta(self):
        result, _log = self._ask("Hola", conversation("Hola " * 200))
        self.assertLessEqual(len(result["reply"]), REPLY_MAX_CHARS + 1)
        self.assertTrue(result["reply"].endswith("…"))

    def test_usuario_sin_permisos_puede_conversar(self):
        user = new_test_user(self.env, login="conversa.sin.grupos", groups="base.group_user")
        result, log = self._ask("Hola", conversation("¡Hola!"), user_env=self.env(user=user))
        self.assertEqual((result["reply"], log.outcome), ("¡Hola!", "conversation"))

    def test_hola_en_discuss(self):
        bot = self.env.ref("chatbot_assistant.partner_chatbot_assistant")
        channel = self.env["discuss.channel"].with_user(self.tester).channel_get([bot.id])
        with patch(COMPLETE_JSON, side_effect=fake_llm(conversation("¡Hola! ¿En qué te ayudo?"))):
            channel.with_user(self.tester).message_post(
                body="Hola", message_type="comment", subtype_xmlid="mail.mt_comment",
            )
        reply = channel.message_ids.filtered(lambda m: m.author_id == bot)[:1]
        self.assertIn("¿En qué te ayudo?", reply.body)
