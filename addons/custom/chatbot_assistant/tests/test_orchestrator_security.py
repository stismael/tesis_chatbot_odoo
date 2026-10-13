# -*- coding: utf-8 -*-
from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import new_test_user
from odoo.tools import mute_logger

from ..services.llm_client import USER_MESSAGES
from .common import ChatbotCase, entities

COMPLETE_JSON = "odoo.addons.chatbot_assistant.services.llm_client.complete_json"


def llm_output(intent, status="ready", missing=None, **values):
    return {
        "intent": intent,
        "entities": entities(**values),
        "status": status,
        "missing_entities": missing or [],
    }


@tagged("post_install", "-at_install", "chatbot_assistant")
class TestOrchestrator(ChatbotCase):
    """Flujo completo con la respuesta del LLM simulada (sin llamadas de red)."""

    def setUp(self):
        super().setUp()
        self.env["ir.config_parameter"].sudo().set_param("chatbot_assistant.api_key", "clave-de-prueba")
        self.user_env = self.env(user=self.tester)
        self.session = self.user_env["chatbot.session"].create({"name": "prueba"})

    def _ask(self, text, output):
        with patch(COMPLETE_JSON, return_value=output) as mocked:
            result = self.user_env["chatbot.orchestrator"].evaluate_query(text, session=self.session)
        return result, mocked

    def test_consulta_lista_se_ejecuta_y_queda_registrada(self):
        result, _mocked = self._ask(
            "¿Quién es el vendedor de Cliente Prueba Uno?",
            llm_output("consultar_vendedor_cliente", customer_name="Cliente Prueba Uno"),
        )
        self.assertTrue(result["success"])
        self.assertIn("Vendedor Prueba", result["reply"])
        log = self.env["chatbot.query.log"].search([("session_id", "=", self.session.id)])
        self.assertEqual(len(log), 1)
        self.assertEqual(log.user_id, self.tester)

    def test_falta_producto_y_luego_se_completa(self):
        result, _mocked = self._ask(
            "¿Cuánto se facturó y cuánto stock hay?",
            llm_output("consultar_stock_facturacion_producto", "missing_information", ["product_name"]),
        )
        self.assertEqual(result["status"], "missing_information")
        self.assertIn(" o ", result["reply"])

        result, _mocked = self._ask(
            "del TST-001",
            llm_output("consultar_stock_facturacion_producto", product_code="TST-001"),
        )
        self.assertEqual(result["status"], "ready")
        self.assertIn("TST-001", result["reply"])

    def test_seguimiento_recuerda_el_producto(self):
        self._ask("stock del TST-001", llm_output("consultar_stock", product_code="TST-001"))
        result, _mocked = self._ask(
            "¿y cuánto se facturó en julio de 2026?",
            llm_output(
                "consultar_stock_facturacion_producto", "missing_information", ["product_name"],
                date_from="2026-07-01", date_to="2026-07-31",
            ),
        )
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["data"]["qty_invoiced"], 3)

    def test_fuera_de_alcance(self):
        result, _mocked = self._ask(
            "Crea una factura", llm_output("fuera_de_alcance", "rejected"),
        )
        self.assertEqual(result["intent"], "fuera_de_alcance")
        self.assertIn("fuera del alcance", result["reply"])

    def test_intencion_inventada_se_rechaza(self):
        result, _mocked = self._ask("borra todo", llm_output("borrar_registros"))
        self.assertEqual(result["intent"], "fuera_de_alcance")

    def test_fecha_actual_se_envia_al_llm(self):
        _result, mocked = self._ask(
            "stock del TST-001", llm_output("consultar_stock", product_code="TST-001"),
        )
        user_payload = mocked.call_args.args[2]
        self.assertIn("Fecha actual:", user_payload)


@tagged("post_install", "-at_install", "chatbot_assistant")
class TestSecurity(ChatbotCase):

    def test_usuario_solo_ve_sus_sesiones_y_consultas(self):
        other = new_test_user(self.env, login="otro.usuario", groups="base.group_user")
        own = self.env(user=self.tester)["chatbot.session"].create({"name": "mia"})
        foreign = self.env(user=other)["chatbot.session"].create({"name": "ajena"})
        self.env["chatbot.query.log"].sudo().create({
            "name": "ajena", "user_id": other.id, "session_id": foreign.id, "query": "x",
        })

        tester_env = self.env(user=self.tester)
        self.assertEqual(tester_env["chatbot.session"].search([]), own)
        self.assertFalse(tester_env["chatbot.query.log"].search([("user_id", "=", other.id)]))
        self.assertFalse(tester_env["chatbot.message"].search([("session_id", "=", foreign.id)]))

    def test_administrador_del_chatbot_ve_todo(self):
        other = new_test_user(self.env, login="otro.usuario", groups="base.group_user")
        foreign = self.env(user=other)["chatbot.session"].create({"name": "ajena"})
        admin_env = self.env(user=self.env.ref("base.user_admin"))
        self.assertIn(foreign, admin_env["chatbot.session"].search([]))

    @mute_logger("odoo.addons.chatbot_assistant.models.chatbot_discuss_service")
    def test_error_interno_no_se_muestra_en_el_chat(self):
        bot = self.env.ref("chatbot_assistant.partner_chatbot_assistant")
        channel = self.env["discuss.channel"].with_user(self.tester).channel_get([bot.id])
        Orchestrator = type(self.env["chatbot.orchestrator"])
        with patch.object(Orchestrator, "process_message", side_effect=RuntimeError("detalle interno secreto")):
            channel.with_user(self.tester).message_post(
                body="¿stock del TST-001?", message_type="comment", subtype_xmlid="mail.mt_comment",
            )
        reply = channel.message_ids.filtered(lambda m: m.author_id == bot)[:1]
        self.assertTrue(reply)
        self.assertNotIn("detalle interno secreto", reply.body)
        self.assertIn(USER_MESSAGES["generic"].split(".")[0], reply.body)
