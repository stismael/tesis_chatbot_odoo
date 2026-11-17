# -*- coding: utf-8 -*-
"""Privacidad: a la IA solo se envían preguntas del usuario y entidades, nunca datos de Odoo."""
from unittest.mock import patch

from odoo.tests import tagged

from .common import ChatbotCase, entities

COMPLETE_JSON = "odoo.addons.chatbot_assistant.services.llm_client.complete_json"


def llm_output(intent, **values):
    return {"intent": intent, "entities": entities(**values), "status": "ready", "missing_entities": []}


@tagged("post_install", "-at_install", "chatbot_assistant")
class TestPrivacyContext(ChatbotCase):

    def setUp(self):
        super().setUp()
        self.env["ir.config_parameter"].sudo().set_param("chatbot_assistant.api_key", "clave-de-prueba")
        self.user_env = self.env(user=self.tester)
        self.session = self.user_env["chatbot.session"].create({"name": "prueba"})

    def _ask(self, text, output):
        with patch(COMPLETE_JSON, return_value=output) as mocked:
            result = self.user_env["chatbot.orchestrator"].evaluate_query(text, session=self.session)
        payload = mocked.call_args.args[2]
        return result, payload

    def test_respuestas_con_datos_no_se_envian_a_la_ia(self):
        first, _payload = self._ask(
            "¿cuánto se vendió a Cliente Prueba Uno?",
            llm_output("consultar_ventas_cliente", customer_name="Cliente Prueba Uno"),
        )
        self.assertIn("1700.00", first["reply"])  # la respuesta sí tiene el monto
        _second, payload = self._ask(
            "¿y quién es su vendedor?", llm_output("consultar_vendedor_cliente", customer_name="Cliente Prueba Uno"),
        )
        self.assertNotIn("1700", payload)
        self.assertNotIn("17 pedido", payload)
        # Sí viajan la pregunta anterior y las entidades para resolver el seguimiento.
        self.assertIn("¿cuánto se vendió a Cliente Prueba Uno?", payload)
        self.assertIn("Cliente Prueba Uno", payload)

    def test_la_pregunta_actual_no_se_repite_en_el_contexto(self):
        self._ask("hola", {"intent": "conversacion", "entities": {}, "status": "ready",
                           "missing_entities": [], "reply": "Hola"})
        _result, payload = self._ask(
            "stock del TST-001", llm_output("consultar_stock", product_code="TST-001"),
        )
        self.assertEqual(payload.count("stock del TST-001"), 1)
        context = self.session.get_short_context()
        self.assertEqual(context["recent_questions"], ["hola"])
        self.assertNotIn("recent_messages", context)
