# -*- coding: utf-8 -*-
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tools.safe_eval import safe_eval

from ..services import llm_client
from ..services.llm_client import ChatbotLLMError, LLMClientError
from .common import ChatbotCase

TEST_CONNECTION = "odoo.addons.chatbot_assistant.services.llm_client.test_connection"
LIST_MODELS = "odoo.addons.chatbot_assistant.services.llm_client.list_models"


def model_item(model_id, **values):
    return dict({"id": model_id, "display_name": model_id, "description": "", "input_token_limit": 1000,
                 "output_token_limit": 100}, **values)


def connection_ok(config):
    return {"ok": True, "provider": config["provider"], "model": config["model"], "latency_ms": 5,
            "message": "Conexión exitosa", "models": []}


@tagged("post_install", "-at_install", "chatbot_assistant")
class TestModelSelection(ChatbotCase):

    def setUp(self):
        super().setUp()
        self.ICP = self.env["ir.config_parameter"].sudo()
        self.ICP.set_param("chatbot_assistant.api_key", "clave-de-prueba")
        self.ICP.set_param("chatbot_assistant.provider", "gemini")
        self.ICP.set_param("chatbot_assistant.model", "gemini-2.5-flash")
        self.ICP.set_param("chatbot_assistant.active", "True")
        self.Model = self.env["chatbot.llm.model"]
        self.gemini_flash = self.env.ref("chatbot_assistant.llm_model_gemini_25_flash")
        self.groq_llama = self.env.ref("chatbot_assistant.llm_model_groq_llama_33_70b")

    def _save(self, values, connection=connection_ok):
        settings = self.env["res.config.settings"].create(values)
        with patch(TEST_CONNECTION, side_effect=connection) as mocked:
            settings.execute()
        return mocked

    # Cambio de proveedor -----------------------------------------------------

    def test_cambio_de_proveedor_usa_siempre_el_recomendado(self):
        for model in ("llama-3.3-70b-versatile", "openai/gpt-oss-120b", "qwen/qwen3-32b",
                      "deepseek-r1-distill-llama-70b"):
            settings = self.env["res.config.settings"].new({"chatbot_provider": "groq", "chatbot_model": model})
            settings.chatbot_provider = "gemini"
            settings._onchange_chatbot_provider()
            self.assertEqual(settings.chatbot_model, "gemini-2.5-flash", model)
            self.assertEqual(settings.chatbot_llm_model_id, self.gemini_flash)

        settings = self.env["res.config.settings"].new({"chatbot_provider": "gemini", "chatbot_model": "gemini-2.5-pro"})
        settings.chatbot_provider = "groq"
        settings._onchange_chatbot_provider()
        self.assertEqual(settings.chatbot_model, "llama-3.3-70b-versatile")
        self.assertEqual(settings.chatbot_llm_model_id, self.groq_llama)

    # Catálogo -----------------------------------------------------------------

    def test_sincronizacion_agrega_actualiza_marca_y_reactiva(self):
        counts = self.Model._sync_provider("groq", [
            model_item("llama-3.3-70b-versatile", input_token_limit=131072),
            model_item("qwen/qwen3-32b"),
        ])
        self.assertEqual((counts["added"], counts["updated"]), (1, 1))
        self.assertEqual(self.groq_llama.input_token_limit, 131072)
        qwen = self.Model._find("groq", "qwen/qwen3-32b")
        self.assertTrue(qwen.available)

        counts = self.Model._sync_provider("groq", [model_item("llama-3.3-70b-versatile")])
        self.assertEqual(counts["unavailable"], 1)
        self.assertTrue(qwen.exists(), "La sincronización no borra modelos")
        self.assertFalse(qwen.available)
        self.assertTrue(self.gemini_flash.available, "Solo se toca el proveedor consultado")

        counts = self.Model._sync_provider("groq", [model_item("llama-3.3-70b-versatile"), model_item("qwen/qwen3-32b")])
        self.assertEqual(counts["reactivated"], 1)
        self.assertTrue(qwen.available)
        self.assertTrue(self.ICP.get_param("chatbot_assistant.models_synced_groq"))

    def test_desplegable_solo_muestra_disponibles_del_proveedor(self):
        self.Model._sync_provider("groq", [model_item("llama-3.3-70b-versatile"), model_item("qwen/qwen3-32b")])
        self.Model._sync_provider("groq", [model_item("llama-3.3-70b-versatile")])
        domain = self.env["res.config.settings"]._fields["chatbot_llm_model_id"].domain
        options = self.Model.search(safe_eval(domain, {"chatbot_provider": "groq"}))
        self.assertEqual(options, self.groq_llama)
        options = self.Model.search(safe_eval(domain, {"chatbot_provider": "gemini"}))
        self.assertEqual(options, self.gemini_flash)

    def test_boton_actualizar_modelos(self):
        settings = self.env["res.config.settings"].create({})
        with patch(LIST_MODELS, return_value=[model_item("gemini-2.5-flash"), model_item("gemini-2.5-pro")]):
            action = settings.action_chatbot_sync_models()
        self.assertIn("Nuevos: 1", action["params"]["message"])
        self.assertTrue(self.Model._find("gemini", "gemini-2.5-pro"))

    def test_aviso_si_el_modelo_configurado_ya_no_esta_disponible(self):
        self.gemini_flash.available = False
        settings = self.env["res.config.settings"].create({})
        self.assertIn("ya no está disponible en Google Gemini", settings.chatbot_model_warning)
        self.gemini_flash.available = True
        self.assertFalse(self.env["res.config.settings"].create({}).chatbot_model_warning)

    # Validación al guardar ------------------------------------------------------

    def test_guardar_con_conexion_fallida_no_guarda(self):
        def fail(config):
            raise LLMClientError("auth")
        with self.assertRaisesRegex(UserError, "(?s)No se guardó la configuración.*API Key inválida"):
            self._save({"chatbot_provider": "groq", "chatbot_llm_model_id": self.groq_llama.id}, fail)
        self.assertEqual(self.ICP.get_param("chatbot_assistant.provider"), "gemini")

    def test_guardar_con_conexion_correcta_guarda_y_registra_la_verificacion(self):
        mocked = self._save({"chatbot_provider": "groq", "chatbot_llm_model_id": self.groq_llama.id})
        self.assertEqual(mocked.call_count, 1)
        self.assertEqual(self.ICP.get_param("chatbot_assistant.provider"), "groq")
        self.assertEqual(self.ICP.get_param("chatbot_assistant.model"), "llama-3.3-70b-versatile")
        self.assertIn("Conexión verificada el", self.ICP.get_param("chatbot_assistant.last_verified"))
        self.assertIn("llama-3.3-70b-versatile", self.ICP.get_param("chatbot_assistant.last_verified"))

    def test_desactivar_no_prueba_la_conexion(self):
        def fail(config):
            raise LLMClientError("network")
        mocked = self._save({"chatbot_active": False, "chatbot_provider": "groq",
                             "chatbot_llm_model_id": self.groq_llama.id}, fail)
        self.assertFalse(mocked.called)
        # El asistente debe quedar apagado de verdad y así debe verse al volver a Ajustes.
        self.assertEqual(self.ICP.get_param("chatbot_assistant.active"), "False")
        self.assertFalse(llm_client.get_chatbot_config(self.env)["active"])
        self.assertFalse(self.env["res.config.settings"].create({}).chatbot_active)
        with self.assertRaises(ChatbotLLMError) as error:
            llm_client.complete_json(self.env, "sistema", "usuario")
        self.assertEqual(error.exception.code, "inactive")
        self._save({"chatbot_active": True})
        self.assertEqual(self.ICP.get_param("chatbot_assistant.active"), "True")

    def test_cambiar_solo_otros_datos_no_prueba_la_conexion(self):
        mocked = self._save({"chatbot_temperature": 0.3, "chatbot_timeout": 25})
        self.assertFalse(mocked.called)
        self.assertEqual(self.ICP.get_param("chatbot_assistant.timeout"), "25")

    def test_modelo_de_otro_proveedor(self):
        with self.assertRaisesRegex(UserError, "'llama-3.3-70b-versatile' no pertenece a Google Gemini"):
            self._save({"chatbot_llm_model_id": False, "chatbot_model": "llama-3.3-70b-versatile"})

    # Estado del proveedor -------------------------------------------------------

    def test_estado_muestra_la_ultima_falla(self):
        Log = self.env["chatbot.query.log"].sudo()
        self.assertEqual(self.env["res.config.settings"].create({}).chatbot_llm_status, "Sin fallas registradas.")
        Log.create({"name": "falla", "user_id": self.tester.id, "query": "x", "outcome": "llm_unavailable",
                    "error_code": "rate_limit", "llm_model": "gemini-2.5-flash"})
        status = self.env["res.config.settings"].create({}).chatbot_llm_status
        self.assertIn("Cuota agotada (429)", status)
        self.assertIn("gemini-2.5-flash", status)
