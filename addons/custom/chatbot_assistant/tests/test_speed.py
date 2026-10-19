# -*- coding: utf-8 -*-
import importlib.util
from pathlib import Path
from unittest.mock import patch

from odoo.tests import tagged

from ..models.orchestrator import OUT_OF_SCOPE_MSG
from ..services import llm_client
from ..services.llm_client import USER_MESSAGES, ChatbotLLMError
from ..services.prompt_builder import RESPONSE_SCHEMA
from .common import ChatbotCase
from .test_metrics import fake_llm
from .test_orchestrator_security import COMPLETE_JSON, llm_output

MIGRATION = Path(__file__).resolve().parents[1] / "migrations" / "18.0.1.7.0" / "post-migrate.py"


@tagged("post_install", "-at_install", "chatbot_assistant")
class TestSpeed(ChatbotCase):

    def setUp(self):
        super().setUp()
        self.ICP = self.env["ir.config_parameter"].sudo()
        self.ICP.set_param("chatbot_assistant.api_key", "clave-de-prueba")

    def test_el_orquestador_envia_el_esquema_de_respuesta(self):
        session = self.env["chatbot.session"].create({"name": "esquema"})
        with patch(COMPLETE_JSON, return_value=llm_output("consultar_stock", product_code="TST-001")) as mocked:
            self.env["chatbot.orchestrator"].evaluate_query("stock del TST-001", session=session)
        self.assertIs(mocked.call_args.kwargs["response_schema"], RESPONSE_SCHEMA)

    def test_timeout_por_defecto(self):
        self.assertEqual(self.ICP.get_param("chatbot_assistant.timeout"), "20")
        self.assertEqual(llm_client.get_chatbot_config(self.env)["timeout"], 20)

    def test_migracion_baja_el_timeout_antiguo_y_respeta_el_personalizado(self):
        spec = importlib.util.spec_from_file_location("chatbot_migracion_1_7_0", MIGRATION)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)

        def migrate_from(value):
            self.ICP.set_param("chatbot_assistant.timeout", value)
            self.env.flush_all()
            migration.migrate(self.env.cr, "18.0.1.6.0")
            self.env.cr.execute(
                "SELECT value FROM ir_config_parameter WHERE key = 'chatbot_assistant.timeout'"
            )
            return self.env.cr.fetchone()[0]

        self.assertEqual(migrate_from("45"), "20")
        self.assertEqual(migrate_from("30"), "30")

    # "Hola": el chat siempre responde -------------------------------------------

    def _say_hello(self, side_effect):
        bot = self.env.ref("chatbot_assistant.partner_chatbot_assistant")
        channel = self.env["discuss.channel"].with_user(self.tester).channel_get([bot.id])
        with patch(COMPLETE_JSON, side_effect=side_effect):
            channel.with_user(self.tester).message_post(
                body="Hola", message_type="comment", subtype_xmlid="mail.mt_comment",
            )
        reply = channel.message_ids.filtered(lambda m: m.author_id == bot)[:1]
        log = self.env["chatbot.query.log"].search([("reply_message_id", "=", reply.id)])
        return reply, log

    def test_hola_recibe_respuesta(self):
        reply, log = self._say_hello(fake_llm(llm_output("fuera_de_alcance", "rejected")))
        self.assertIn("fuera del alcance", reply.body)
        self.assertEqual(log.outcome, "rejected")
        self.assertEqual(log.reply, OUT_OF_SCOPE_MSG)

    def test_hola_con_la_ia_caida_tambien_responde(self):
        reply, log = self._say_hello(ChatbotLLMError(USER_MESSAGES["timeout"], "timeout"))
        self.assertIn("no pude responder a tiempo", reply.body)
        self.assertEqual((log.outcome, log.error_code), ("llm_unavailable", "timeout"))
