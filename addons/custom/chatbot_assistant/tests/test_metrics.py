# -*- coding: utf-8 -*-
from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import new_test_user
from odoo.tools import mute_logger

from ..models.orchestrator import FORBIDDEN_MSG
from ..services.handlers import HANDLER_MAP
from ..services.llm_client import USER_MESSAGES, ChatbotLLMError
from .common import ChatbotCase, entities
from .test_orchestrator_security import COMPLETE_JSON, llm_output


def fake_llm(output, **meta_values):
    """Simula la IA: devuelve `output` y completa los metadatos como lo haría llm_client."""
    def _fake(env, system_prompt, user_message, meta=None, response_schema=None):
        if meta is not None:
            meta.update({
                "provider": "gemini", "model": "gemini-2.5-flash", "retries": 0,
                "tokens_prompt": 1200, "tokens_output": 80, "tokens_thinking": 0,
            })
            meta.update(meta_values)
        return output
    return _fake


@tagged("post_install", "-at_install", "chatbot_assistant")
class TestMetrics(ChatbotCase):

    def setUp(self):
        super().setUp()
        self.env["ir.config_parameter"].sudo().set_param("chatbot_assistant.api_key", "clave-de-prueba")

    def _ask(self, text, side_effect, user=None):
        user_env = self.env(user=user or self.tester)
        session = user_env["chatbot.session"].create({"name": "metricas"})
        with patch(COMPLETE_JSON, side_effect=side_effect):
            result = user_env["chatbot.orchestrator"].evaluate_query(text, session=session)
        log = self.env["chatbot.query.log"].browse(result["log_id"])
        return result, log

    # Resultado clasificado ---------------------------------------------------

    def test_respondida_con_datos_y_metadatos(self):
        _result, log = self._ask(
            "vendedor de Cliente Prueba Uno",
            fake_llm(llm_output("consultar_vendedor_cliente", customer_name="Cliente Prueba Uno"),
                     retries=1, tokens_thinking=300),
        )
        self.assertEqual(log.outcome, "answered")
        self.assertFalse(log.error_code)
        self.assertEqual(log.llm_provider, "gemini")
        self.assertEqual(log.llm_model, "gemini-2.5-flash")
        self.assertEqual(log.retries, 1)
        self.assertEqual((log.tokens_prompt, log.tokens_output, log.tokens_thinking), (1200, 80, 300))

    def test_tiempos_por_etapa(self):
        _result, log = self._ask(
            "stock del TST-001",
            fake_llm(llm_output("consultar_stock", product_code="TST-001")),
        )
        self.assertGreaterEqual(log.llm_ms, 0)
        self.assertGreaterEqual(log.orm_ms, 0)
        self.assertGreaterEqual(log.latency_ms, log.llm_ms)
        self.assertGreaterEqual(log.latency_ms, log.orm_ms)

    def test_sin_resultados(self):
        _result, log = self._ask(
            "factura INV/1999/99999",
            fake_llm(llm_output("consultar_factura", invoice_number="INV/1999/99999")),
        )
        self.assertEqual(log.outcome, "no_results")

    def test_aclaracion_pedida(self):
        _result, log = self._ask(
            "¿cuánto stock hay?",
            fake_llm(llm_output("consultar_stock", "missing_information", ["product_name"])),
        )
        self.assertEqual(log.outcome, "clarification")

    def test_aclaracion_por_ambiguedad_del_handler(self):
        _result, log = self._ask(
            "ventas de Distribuidora Similar",
            fake_llm(llm_output("consultar_ventas_cliente", customer_name="Distribuidora Similar")),
        )
        self.assertEqual(log.outcome, "clarification")

    def test_rechazada(self):
        _result, log = self._ask("crea una factura", fake_llm(llm_output("fuera_de_alcance", "rejected")))
        self.assertEqual(log.outcome, "rejected")

    def test_intencion_inventada(self):
        _result, log = self._ask("borra todo", fake_llm(llm_output("borrar_registros")))
        self.assertEqual((log.outcome, log.error_code), ("llm_bad_output", "unknown_intent"))

    def test_salida_no_valida(self):
        _result, log = self._ask(
            "stock", fake_llm(llm_output("consultar_stock", "estado_raro", product_code="TST-001")),
        )
        self.assertEqual((log.outcome, log.error_code), ("llm_bad_output", "invalid_output"))

    def test_ia_no_disponible(self):
        for code in ("timeout", "rate_limit", "server", "network", "auth", "model", "missing_key"):
            error = ChatbotLLMError(USER_MESSAGES.get(code, USER_MESSAGES["generic"]), code)
            result, log = self._ask("stock del TST-001", error)
            self.assertEqual((log.outcome, log.error_code), ("llm_unavailable", code), code)
            self.assertEqual(result["reply"], error.args[0])

    def test_ia_respondio_json_invalido(self):
        error = ChatbotLLMError(USER_MESSAGES["invalid_json"], "invalid_json")
        _result, log = self._ask("stock del TST-001", error)
        self.assertEqual((log.outcome, log.error_code), ("llm_bad_output", "invalid_json"))

    def test_sin_permiso_mensaje_en_espanol(self):
        # Sin grupos exigidos en la tabla, la consulta llega a Odoo, que niega el acceso.
        self.env.ref("chatbot_assistant.permission_consultar_factura").group_ids = [(5, 0, 0)]
        plain_user = new_test_user(self.env, login="sin.grupos", groups="base.group_user")
        result, log = self._ask(
            "factura", fake_llm(llm_output("consultar_factura", customer_name="Cliente Prueba Uno")),
            user=plain_user,
        )
        self.assertEqual((log.outcome, log.error_code), ("forbidden", "access"))
        self.assertEqual(result["reply"], FORBIDDEN_MSG)
        self.assertNotIn("not allowed", result["reply"])
        self.assertTrue(log.error, "El detalle técnico debe quedar en el log")

    @mute_logger("odoo.addons.chatbot_assistant.models.orchestrator")
    def test_error_interno(self):
        def broken_handler(env, values, user_text=""):
            raise ValueError("fallo de prueba")
        with patch.dict(HANDLER_MAP, {"consultar_stock": broken_handler}):
            result, log = self._ask(
                "stock del TST-001", fake_llm(llm_output("consultar_stock", product_code="TST-001")),
            )
        self.assertEqual((log.outcome, log.error_code), ("internal_error", "generic"))
        self.assertEqual(result["reply"], USER_MESSAGES["generic"])

    # Valoración del usuario --------------------------------------------------

    def test_reacciones_en_discuss_registran_la_valoracion(self):
        bot = self.env.ref("chatbot_assistant.partner_chatbot_assistant")
        channel = self.env["discuss.channel"].with_user(self.tester).channel_get([bot.id])
        output = llm_output("consultar_vendedor_cliente", customer_name="Cliente Prueba Uno")
        with patch(COMPLETE_JSON, side_effect=fake_llm(output)):
            channel.with_user(self.tester).message_post(
                body="¿Quién es el vendedor de Cliente Prueba Uno?",
                message_type="comment", subtype_xmlid="mail.mt_comment",
            )
        reply = channel.message_ids.filtered(lambda m: m.author_id == bot)[:1]
        log = self.env["chatbot.query.log"].search([("reply_message_id", "=", reply.id)])
        self.assertEqual(len(log), 1, "La respuesta del bot debe quedar ligada a su log")
        self.assertFalse(log.user_feedback)

        Reaction = self.env["mail.message.reaction"].sudo()
        thumbs_up = Reaction.create({
            "message_id": reply.id, "content": "\U0001F44D", "partner_id": self.tester.partner_id.id,
        })
        self.assertEqual(log.user_feedback, "up")

        Reaction.create({
            "message_id": reply.id, "content": "\U0001F44E", "partner_id": self.tester.partner_id.id,
        })
        self.assertEqual(log.user_feedback, "down")

        reply.sudo().reaction_ids.filtered(lambda r: r.content == "\U0001F44E").unlink()
        self.assertEqual(log.user_feedback, "up")
        thumbs_up.unlink()
        self.assertFalse(log.user_feedback)

    # Retención ---------------------------------------------------------------

    def test_limpieza_por_antiguedad(self):
        Log = self.env["chatbot.query.log"].sudo()
        old = Log.create({"name": "vieja", "user_id": self.tester.id, "query": "x"})
        recent = Log.create({"name": "reciente", "user_id": self.tester.id, "query": "y"})
        old_date = fields.Datetime.now() - timedelta(days=40)
        self.env.cr.execute("UPDATE chatbot_query_log SET create_date = %s WHERE id = %s", (old_date, old.id))
        Log.invalidate_model(["create_date"])

        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("chatbot_assistant.log_retention_days", "0")
        self.assertEqual(Log._cron_purge_old_logs(), 0)
        self.assertTrue(old.exists())

        ICP.set_param("chatbot_assistant.log_retention_days", "30")
        Log._cron_purge_old_logs()
        self.assertFalse(old.exists())
        self.assertTrue(recent.exists())
