# -*- coding: utf-8 -*-
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged
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
        self.ICP.set_param("chatbot_assistant.model", "gemini-3.1-flash-lite")
        self.ICP.set_param("chatbot_assistant.active", "True")
        self.Model = self.env["chatbot.llm.model"]
        self.gemini_flash = self.env.ref("chatbot_assistant.llm_model_gemini_31_flash_lite")
        self.groq_default = self.env.ref("chatbot_assistant.llm_model_groq_gpt_oss_120b")

    def _save(self, values, connection=connection_ok):
        settings = self.env["res.config.settings"].create(values)
        with patch(TEST_CONNECTION, side_effect=connection) as mocked:
            settings.execute()
        return mocked

    # Cambio de proveedor -----------------------------------------------------

    def test_cambio_de_proveedor_usa_siempre_el_recomendado(self):
        for model in ("openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3-32b",
                      "deepseek-r1-distill-llama-70b"):
            settings = self.env["res.config.settings"].new({
                "chatbot_provider": "groq", "chatbot_model": model, "chatbot_api_key": "gsk_old",
            })
            settings.chatbot_provider = "gemini"
            settings._onchange_chatbot_provider()
            # Gemini es el proveedor guardado: se muestra su configuración (modelo y clave guardados).
            self.assertEqual(settings.chatbot_model, "gemini-3.1-flash-lite", model)
            self.assertEqual(settings.chatbot_llm_model_id, self.gemini_flash)
            self.assertEqual(settings.chatbot_api_key, "clave-de-prueba")

        settings = self.env["res.config.settings"].new({
            "chatbot_provider": "gemini", "chatbot_model": "gemini-2.5-pro", "chatbot_api_key": "AIzaOld",
        })
        settings.chatbot_provider = "groq"
        settings._onchange_chatbot_provider()
        self.assertEqual(settings.chatbot_model, "openai/gpt-oss-120b")
        self.assertEqual(settings.chatbot_llm_model_id, self.groq_default)
        self.assertFalse(settings.chatbot_api_key, "Al cambiar a otro proveedor se vacía la API Key")

    # Catálogo -----------------------------------------------------------------

    def test_sincronizacion_agrega_actualiza_marca_y_reactiva(self):
        counts = self.Model._sync_provider("groq", [
            model_item("openai/gpt-oss-120b", input_token_limit=131072),
            model_item("qwen/qwen3-32b"),
        ])
        self.assertEqual((counts["added"], counts["updated"]), (1, 1))
        self.assertEqual(self.groq_default.input_token_limit, 131072)
        qwen = self.Model._find("groq", "qwen/qwen3-32b")
        self.assertTrue(qwen.available)

        counts = self.Model._sync_provider("groq", [model_item("openai/gpt-oss-120b")])
        self.assertEqual(counts["unavailable"], 1)
        self.assertTrue(qwen.exists(), "La sincronización no borra modelos")
        self.assertFalse(qwen.available)
        self.assertTrue(self.gemini_flash.available, "Solo se toca el proveedor consultado")

        counts = self.Model._sync_provider("groq", [model_item("openai/gpt-oss-120b"), model_item("qwen/qwen3-32b")])
        self.assertEqual(counts["reactivated"], 1)
        self.assertTrue(qwen.available)
        self.assertTrue(self.ICP.get_param("chatbot_assistant.models_synced_groq"))

    def test_desplegable_solo_muestra_disponibles_del_proveedor(self):
        self.Model._sync_provider("groq", [model_item("openai/gpt-oss-120b"), model_item("qwen/qwen3-32b")])
        self.Model._sync_provider("groq", [model_item("openai/gpt-oss-120b")])
        domain = self.env["res.config.settings"]._fields["chatbot_llm_model_id"].domain
        options = self.Model.search(safe_eval(domain, {"chatbot_provider": "groq"}))
        self.assertEqual(options, self.groq_default)
        options = self.Model.search(safe_eval(domain, {"chatbot_provider": "gemini"}))
        self.assertEqual(options, self.gemini_flash)

    def test_boton_actualizar_modelos(self):
        settings = self.env["res.config.settings"].create({})
        with patch(LIST_MODELS, return_value=[model_item("gemini-3.1-flash-lite"), model_item("gemini-2.5-pro")]):
            action = settings.action_chatbot_sync_models()
        self.assertIn("Nuevos: 1", action["params"]["message"])
        pro = self.Model._find("gemini", "gemini-2.5-pro")
        self.assertTrue(pro)
        self.assertEqual(pro.pricing_hint, "paid")
        self.assertEqual(self.Model._find("gemini", "gemini-3.1-flash-lite").pricing_hint, "free")

    def test_pricing_hint_heuristics(self):
        self.assertEqual(llm_client.pricing_hint("gemini", "gemini-3.1-flash-lite"), "free")
        self.assertEqual(llm_client.pricing_hint("gemini", "gemini-2.5-pro"), "paid")
        self.assertEqual(llm_client.pricing_hint("groq", "openai/gpt-oss-120b"), "free")

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
            self._save({"chatbot_provider": "groq", "chatbot_api_key": "gsk_prueba",
                        "chatbot_llm_model_id": self.groq_default.id}, fail)
        self.assertEqual(self.ICP.get_param("chatbot_assistant.provider"), "gemini")

    def test_guardar_con_conexion_correcta_guarda_y_registra_la_verificacion(self):
        mocked = self._save({"chatbot_provider": "groq", "chatbot_api_key": "gsk_prueba",
                             "chatbot_llm_model_id": self.groq_default.id})
        self.assertEqual(mocked.call_count, 1)
        self.assertEqual(self.ICP.get_param("chatbot_assistant.provider"), "groq")
        self.assertEqual(self.ICP.get_param("chatbot_assistant.model"), "openai/gpt-oss-120b")
        self.assertIn("Conexión verificada el", self.ICP.get_param("chatbot_assistant.last_verified"))
        self.assertIn("openai/gpt-oss-120b", self.ICP.get_param("chatbot_assistant.last_verified"))

    def test_desactivar_no_prueba_la_conexion(self):
        def fail(config):
            raise LLMClientError("network")
        mocked = self._save({"chatbot_active": False, "chatbot_provider": "groq",
                             "chatbot_llm_model_id": self.groq_default.id}, fail)
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

    def test_volver_al_proveedor_original_no_borra_la_api_key(self):
        # En el formulario: Gemini -> Groq (el onchange vacía la key) -> Gemini, sin pegar la clave.
        settings = self.env["res.config.settings"].new({"chatbot_provider": "gemini", "chatbot_api_key": "clave-de-prueba"})
        settings.chatbot_provider = "groq"
        settings._onchange_chatbot_provider()
        settings.chatbot_provider = "gemini"
        settings._onchange_chatbot_provider()
        self.assertEqual(settings.chatbot_api_key, "clave-de-prueba", "Al volver se muestra la clave guardada")
        # Aunque el campo llegue vacío al guardar, la clave guardada no se borra.
        mocked = self._save({"chatbot_provider": "gemini", "chatbot_api_key": False, "chatbot_temperature": 0.2})
        self.assertFalse(mocked.called)
        self.assertEqual(self.ICP.get_param("chatbot_assistant.api_key"), "clave-de-prueba")

    def test_clave_de_otro_proveedor_se_rechaza_al_guardar(self):
        with self.assertRaisesRegex(UserError, "parece de Google Gemini"):
            self._save({"chatbot_provider": "groq", "chatbot_api_key": "AIzaClaveDeGemini",
                        "chatbot_llm_model_id": self.groq_default.id})
        self.assertEqual(self.ICP.get_param("chatbot_assistant.provider"), "gemini")

    def test_abrir_ajustes_muestra_el_modelo_guardado(self):
        # Al abrir Ajustes, Odoo ejecuta el onchange del proveedor: no debe reemplazar el modelo guardado.
        self.Model._sync_provider("gemini", [model_item("gemini-3.1-flash-lite"), model_item("gemini-2.5-pro")])
        self.ICP.set_param("chatbot_assistant.model", "gemini-2.5-pro")
        settings = self.env["res.config.settings"].new({"chatbot_provider": "gemini"})
        settings._onchange_chatbot_provider()
        self.assertEqual(settings.chatbot_model, "gemini-2.5-pro")
        self.assertEqual(settings.chatbot_llm_model_id, self.Model._find("gemini", "gemini-2.5-pro"))
        # Guardar otro dato no cambia el modelo.
        mocked = self._save({"chatbot_llm_model_id": settings.chatbot_llm_model_id.id, "chatbot_temperature": 0.2})
        self.assertFalse(mocked.called)
        self.assertEqual(self.ICP.get_param("chatbot_assistant.model"), "gemini-2.5-pro")

    def test_probar_conexion_no_cambia_la_configuracion_activa(self):
        settings = self.env["res.config.settings"].create({
            "chatbot_provider": "groq", "chatbot_api_key": "gsk_prueba",
            "chatbot_llm_model_id": self.groq_default.id,
        })
        with patch(TEST_CONNECTION, side_effect=connection_ok):
            action = settings.action_chatbot_test_connection()
        self.assertEqual(action["params"]["type"], "success")
        # El chat sigue con lo guardado hasta pulsar Guardar.
        self.assertEqual(self.ICP.get_param("chatbot_assistant.provider"), "gemini")
        self.assertEqual(self.ICP.get_param("chatbot_assistant.api_key"), "clave-de-prueba")
        self.assertEqual(self.ICP.get_param("chatbot_assistant.model"), "gemini-3.1-flash-lite")
        self.assertFalse(self.ICP.get_param("chatbot_assistant.last_verified"))
        # El formulario sí muestra la verificación y conserva lo escrito.
        self.assertIn("openai/gpt-oss-120b", settings.chatbot_last_verified)
        self.assertEqual((settings.chatbot_provider, settings.chatbot_api_key), ("groq", "gsk_prueba"))

    def test_actualizar_modelos_no_cambia_la_configuracion_activa(self):
        settings = self.env["res.config.settings"].create({"chatbot_provider": "groq", "chatbot_api_key": "gsk_prueba"})
        with patch(LIST_MODELS, return_value=[model_item("openai/gpt-oss-120b"), model_item("qwen/qwen3-32b")]):
            settings.action_chatbot_sync_models()
        self.assertTrue(self.Model._find("groq", "qwen/qwen3-32b"), "El catálogo sí se actualiza")
        self.assertEqual(self.ICP.get_param("chatbot_assistant.provider"), "gemini")
        self.assertEqual(self.ICP.get_param("chatbot_assistant.api_key"), "clave-de-prueba")

    def test_guardar_despues_de_probar_aplica_la_configuracion(self):
        settings = self.env["res.config.settings"].create({
            "chatbot_provider": "groq", "chatbot_api_key": "gsk_prueba",
            "chatbot_llm_model_id": self.groq_default.id,
        })
        with patch(TEST_CONNECTION, side_effect=connection_ok) as mocked:
            settings.action_chatbot_test_connection()
            settings.execute()
        self.assertEqual(mocked.call_count, 2, "Al Guardar se vuelve a probar la conexión")
        self.assertEqual(self.ICP.get_param("chatbot_assistant.provider"), "groq")
        self.assertEqual(self.ICP.get_param("chatbot_assistant.api_key"), "gsk_prueba")
        self.assertIn("openai/gpt-oss-120b", self.ICP.get_param("chatbot_assistant.last_verified"))

    def test_cambiar_solo_otros_datos_no_prueba_la_conexion(self):
        mocked = self._save({"chatbot_temperature": 0.3, "chatbot_timeout": 25})
        self.assertFalse(mocked.called)
        self.assertEqual(self.ICP.get_param("chatbot_assistant.timeout"), "25")

    def test_modelo_de_otro_proveedor(self):
        with self.assertRaisesRegex(UserError, "'openai/gpt-oss-120b' no pertenece a Google Gemini"):
            self._save({"chatbot_llm_model_id": False, "chatbot_model": "openai/gpt-oss-120b"})

    # Estado del proveedor -------------------------------------------------------

    def test_estado_muestra_la_ultima_falla(self):
        Log = self.env["chatbot.query.log"].sudo()
        self.assertEqual(self.env["res.config.settings"].create({}).chatbot_llm_status, "Sin fallas registradas.")
        Log.create({"name": "falla", "user_id": self.tester.id, "query": "x", "outcome": "llm_unavailable",
                    "error_code": "rate_limit", "llm_model": "gemini-3.1-flash-lite"})
        status = self.env["res.config.settings"].create({}).chatbot_llm_status
        self.assertIn("Cuota agotada (429)", status)
        self.assertIn("gemini-3.1-flash-lite", status)


@tagged("post_install", "-at_install", "chatbot_assistant")
class TestRetiredGroqModel(TransactionCase):
    """Groq retiró llama-3.3-70b-versatile: la actualización mueve la configuración guardada al recomendado."""

    def test_configuracion_con_modelo_retirado_se_actualiza(self):
        icp = self.env["ir.config_parameter"].sudo()
        for key, value in (("provider", "groq"), ("model", "llama-3.3-70b-versatile"),
                           ("fallback_provider", "groq"), ("fallback_model", "llama-3.3-70b-versatile")):
            icp.set_param("chatbot_assistant." + key, value)
        Model = self.env["chatbot.llm.model"]
        Model.search([("provider", "=", "groq"), ("model_id", "=", llm_client.DEFAULT_GROQ_MODEL)]).unlink()
        changed = Model._replace_retired_models()
        self.assertEqual(changed, ["chatbot_assistant.model", "chatbot_assistant.fallback_model"])
        self.assertEqual(icp.get_param("chatbot_assistant.model"), "openai/gpt-oss-120b")
        self.assertEqual(icp.get_param("chatbot_assistant.fallback_model"), "openai/gpt-oss-120b")
        self.assertTrue(Model._find("groq", "openai/gpt-oss-120b"))

    def test_gemini_retirado_tambien_se_actualiza(self):
        icp = self.env["ir.config_parameter"].sudo()
        icp.set_param("chatbot_assistant.provider", "gemini")
        icp.set_param("chatbot_assistant.model", "gemini-2.5-flash")
        icp.set_param("chatbot_assistant.fallback_provider", "groq")
        icp.set_param("chatbot_assistant.fallback_model", "openai/gpt-oss-20b")
        self.assertEqual(self.env["chatbot.llm.model"]._replace_retired_models(), ["chatbot_assistant.model"])
        self.assertEqual(icp.get_param("chatbot_assistant.model"), "gemini-3.1-flash-lite")
        self.assertEqual(icp.get_param("chatbot_assistant.fallback_model"), "openai/gpt-oss-20b")

    def test_no_toca_otros_modelos_ni_gemini(self):
        icp = self.env["ir.config_parameter"].sudo()
        icp.set_param("chatbot_assistant.provider", "gemini")
        icp.set_param("chatbot_assistant.model", "gemini-3.1-flash-lite")
        icp.set_param("chatbot_assistant.fallback_provider", "groq")
        icp.set_param("chatbot_assistant.fallback_model", "qwen/qwen3.8-27b")
        self.assertEqual(self.env["chatbot.llm.model"]._replace_retired_models(), [])
        self.assertEqual(icp.get_param("chatbot_assistant.fallback_model"), "qwen/qwen3.8-27b")
