# -*- coding: utf-8 -*-
import json
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import tagged

from ..services import llm_client
from ..services.llm_client import ChatbotLLMError, LLMClientError
from .common import ChatbotCase
from .test_model_selection import LIST_MODELS, TEST_CONNECTION, connection_ok, model_item
from .test_orchestrator_security import llm_output

LLM = "odoo.addons.chatbot_assistant.services.llm_client."


def reply(output=None):
    return json.dumps(output or {"intent": "fuera_de_alcance", "entities": {}, "status": "rejected"})


@tagged("post_install", "-at_install", "chatbot_assistant")
class TestFallbackClient(ChatbotCase):
    """Comportamiento de complete_json con el modelo de respaldo (llamadas HTTP simuladas)."""

    def setUp(self):
        super().setUp()
        self.ICP = self.env["ir.config_parameter"].sudo()
        for key, value in (("provider", "gemini"), ("api_key", "AIzaPRINCIPAL"), ("model", "gemini-2.5-flash"),
                           ("active", "True"), ("fallback_active", "True"), ("fallback_provider", "groq"),
                           ("fallback_api_key", "gsk_RESPALDO"), ("fallback_model", "llama-3.3-70b-versatile")):
            self.ICP.set_param("chatbot_assistant." + key, value)
        sleep = patch(LLM + "time.sleep")
        sleep.start()
        self.addCleanup(sleep.stop)

    def _call(self, gemini, groq):
        meta = {}
        with patch(LLM + "_call_gemini", side_effect=gemini) as g, patch(LLM + "_call_groq", side_effect=groq) as q:
            try:
                result = llm_client.complete_json(self.env, "sistema", "usuario", meta=meta)
            except ChatbotLLMError as exc:
                result = exc
        return result, meta, g, q

    def test_responde_el_respaldo_cuando_el_principal_no_esta_disponible(self):
        for code in ("timeout", "rate_limit", "server", "network", "auth", "model", "forbidden_network"):
            result, meta, g, q = self._call(LLMClientError(code), [reply()])
            self.assertEqual(result["intent"], "fuera_de_alcance", code)
            self.assertEqual(g.call_count, 1, "%s: con respaldo, el principal no se reintenta" % code)
            self.assertEqual(q.call_count, 1, code)
            self.assertTrue(meta["fallback_used"], code)
            self.assertEqual((meta["provider"], meta["model"], meta["primary_error"]),
                             ("groq", "llama-3.3-70b-versatile", code))

    def test_respuesta_defectuosa_no_activa_el_respaldo(self):
        result, meta, g, q = self._call(["esto no es JSON"], [reply()])
        self.assertIsInstance(result, ChatbotLLMError)
        self.assertEqual(result.code, "invalid_json")
        self.assertFalse(q.called)
        self.assertFalse(meta["fallback_used"])

    def test_si_fallan_los_dos_se_informa_el_fallo_del_respaldo(self):
        result, meta, g, q = self._call(LLMClientError("server"), LLMClientError("timeout"))
        self.assertIsInstance(result, ChatbotLLMError)
        self.assertEqual(result.code, "timeout")
        self.assertEqual(q.call_count, 1, "un tiempo agotado del respaldo no se reintenta")
        self.assertEqual(meta["primary_error"], "server")

    def test_el_respaldo_reintenta_una_vez_ante_cuota_agotada(self):
        result, meta, g, q = self._call(LLMClientError("server"), [LLMClientError("rate_limit"), reply()])
        self.assertEqual(result["intent"], "fuera_de_alcance")
        self.assertEqual(q.call_count, 2)

    def test_sin_respaldo_se_mantiene_el_comportamiento_anterior(self):
        self.ICP.set_param("chatbot_assistant.fallback_active", "False")
        result, meta, g, q = self._call(LLMClientError("timeout"), [reply()])
        self.assertEqual(result.code, "timeout")
        self.assertEqual(g.call_count, 2, "sin respaldo, el principal se reintenta una vez")
        self.assertFalse(q.called)

    def test_respaldo_activo_sin_clave_no_se_usa(self):
        self.ICP.set_param("chatbot_assistant.fallback_api_key", False)
        result, meta, g, q = self._call(LLMClientError("server"), [reply()])
        self.assertEqual(result.code, "server")
        self.assertFalse(q.called)

    def test_respaldo_del_mismo_proveedor_usa_la_clave_del_principal(self):
        self.ICP.set_param("chatbot_assistant.fallback_provider", "gemini")
        self.ICP.set_param("chatbot_assistant.fallback_api_key", False)
        self.ICP.set_param("chatbot_assistant.fallback_model", "gemini-2.5-flash-lite")
        result, meta, g, q = self._call([LLMClientError("rate_limit"), reply()], [reply()])
        self.assertEqual(result["intent"], "fuera_de_alcance")
        second = g.call_args_list[1].args[0]
        self.assertEqual((second["model"], second["api_key"]), ("gemini-2.5-flash-lite", "AIzaPRINCIPAL"))

    def test_la_auditoria_registra_el_uso_del_respaldo(self):
        output = json.dumps(llm_output("consultar_stock", product_code="TST-001"))
        session = self.env["chatbot.session"].create({"name": "respaldo"})
        with patch(LLM + "_call_gemini", side_effect=LLMClientError("timeout")), \
                patch(LLM + "_call_groq", return_value=output):
            result = self.env["chatbot.orchestrator"].evaluate_query("stock del TST-001", session=session)
        log = self.env["chatbot.query.log"].browse(result["log_id"])
        self.assertEqual(log.outcome, "answered")
        self.assertTrue(log.fallback_used)
        self.assertEqual(log.primary_error_code, "timeout")
        self.assertEqual((log.llm_provider, log.llm_model), ("groq", "llama-3.3-70b-versatile"))


class FallbackSettingsCase(ChatbotCase):
    """Base común (sin pruebas propias) para la sección «Modelo de respaldo» de Ajustes."""

    def setUp(self):
        super().setUp()
        self.ICP = self.env["ir.config_parameter"].sudo()
        for key, value in (("provider", "gemini"), ("api_key", "AIzaPRINCIPAL"), ("model", "gemini-2.5-flash"),
                           ("active", "True")):
            self.ICP.set_param("chatbot_assistant." + key, value)
        self.groq_llama = self.env.ref("chatbot_assistant.llm_model_groq_llama_33_70b")
        self.gemini_flash = self.env.ref("chatbot_assistant.llm_model_gemini_25_flash")

    def _save(self, values, connection=connection_ok):
        settings = self.env["res.config.settings"].create(values)
        with patch(TEST_CONNECTION, side_effect=connection) as mocked:
            settings.execute()
        return mocked

    def _activate(self):
        return self._save({"chatbot_fallback_active": True, "chatbot_fallback_provider": "groq",
                           "chatbot_fallback_api_key": "gsk_RESPALDO",
                           "chatbot_fallback_llm_model_id": self.groq_llama.id})


@tagged("post_install", "-at_install", "chatbot_assistant")
class TestFallbackSettings(FallbackSettingsCase):
    """Sección «Modelo de respaldo» de Ajustes."""

    def test_activar_el_respaldo_prueba_su_conexion_y_lo_guarda(self):
        mocked = self._activate()
        self.assertEqual(mocked.call_count, 1, "solo se prueba el respaldo: el principal no cambió")
        self.assertEqual(mocked.call_args.args[0]["provider"], "groq")
        self.assertEqual(self.ICP.get_param("chatbot_assistant.fallback_active"), "True")
        self.assertEqual(self.ICP.get_param("chatbot_assistant.fallback_api_key"), "gsk_RESPALDO")
        self.assertEqual(self.ICP.get_param("chatbot_assistant.fallback_model"), "llama-3.3-70b-versatile")
        self.assertIn("llama-3.3-70b-versatile", self.ICP.get_param("chatbot_assistant.fallback_last_verified"))
        self.assertEqual(self.ICP.get_param("chatbot_assistant.provider"), "gemini", "el principal no cambia")

    def test_si_falla_la_prueba_del_respaldo_no_se_guarda(self):
        def fail(config):
            raise LLMClientError("auth")
        with self.assertRaisesRegex(UserError, "(?s)prueba de conexión del modelo de respaldo falló"):
            self._save({"chatbot_fallback_active": True, "chatbot_fallback_provider": "groq",
                        "chatbot_fallback_api_key": "gsk_RESPALDO",
                        "chatbot_fallback_llm_model_id": self.groq_llama.id}, fail)
        self.assertNotEqual(self.ICP.get_param("chatbot_assistant.fallback_active"), "True")

    def test_desactivar_el_respaldo_no_prueba_nada(self):
        self._activate()
        mocked = self._save({"chatbot_fallback_active": False})
        self.assertFalse(mocked.called)
        self.assertEqual(self.ICP.get_param("chatbot_assistant.fallback_active"), "False")
        self.assertFalse(llm_client.get_fallback_config(self.env)["active"])
        self.assertFalse(self.env["res.config.settings"].create({}).chatbot_fallback_active)

    def test_con_el_asistente_apagado_no_se_prueba_el_respaldo(self):
        mocked = self._save({"chatbot_active": False, "chatbot_fallback_active": True,
                             "chatbot_fallback_provider": "groq", "chatbot_fallback_api_key": "gsk_RESPALDO",
                             "chatbot_fallback_llm_model_id": self.groq_llama.id})
        self.assertFalse(mocked.called)

    def test_el_respaldo_no_puede_ser_igual_al_principal(self):
        with self.assertRaisesRegex(UserError, "es el mismo que el principal"):
            self._save({"chatbot_fallback_active": True, "chatbot_fallback_provider": "gemini",
                        "chatbot_fallback_llm_model_id": self.gemini_flash.id})

    def test_clave_de_otro_proveedor_en_el_respaldo(self):
        with self.assertRaisesRegex(UserError, "parece de Google Gemini"):
            self._save({"chatbot_fallback_active": True, "chatbot_fallback_provider": "groq",
                        "chatbot_fallback_api_key": "AIzaEQUIVOCADA",
                        "chatbot_fallback_llm_model_id": self.groq_llama.id})

    def test_la_clave_del_respaldo_se_conserva_si_el_campo_llega_vacio(self):
        self._activate()
        mocked = self._save({"chatbot_fallback_api_key": False, "chatbot_temperature": 0.2})
        self.assertFalse(mocked.called)
        self.assertEqual(self.ICP.get_param("chatbot_assistant.fallback_api_key"), "gsk_RESPALDO")

    def test_cambiar_el_proveedor_del_respaldo_y_volver(self):
        self._activate()
        settings = self.env["res.config.settings"].new({"chatbot_fallback_provider": "groq"})
        settings._onchange_chatbot_fallback_provider()
        self.assertEqual(settings.chatbot_fallback_api_key, "gsk_RESPALDO", "al abrir se ve lo guardado")
        settings.chatbot_fallback_provider = "gemini"
        settings._onchange_chatbot_fallback_provider()
        self.assertEqual(settings.chatbot_fallback_model, "gemini-2.5-flash")
        self.assertFalse(settings.chatbot_fallback_api_key)
        settings.chatbot_fallback_provider = "groq"
        settings._onchange_chatbot_fallback_provider()
        self.assertEqual(settings.chatbot_fallback_llm_model_id, self.groq_llama)
        self.assertEqual(settings.chatbot_fallback_api_key, "gsk_RESPALDO")

    def test_probar_y_actualizar_el_respaldo_no_cambian_la_configuracion(self):
        settings = self.env["res.config.settings"].create({
            "chatbot_fallback_active": True, "chatbot_fallback_provider": "groq",
            "chatbot_fallback_api_key": "gsk_RESPALDO", "chatbot_fallback_llm_model_id": self.groq_llama.id,
        })
        with patch(TEST_CONNECTION, side_effect=connection_ok) as mocked:
            settings.action_chatbot_fallback_test_connection()
        self.assertEqual(mocked.call_args.args[0]["provider"], "groq")
        self.assertIn("llama-3.3-70b-versatile", settings.chatbot_fallback_last_verified)
        with patch(LIST_MODELS, return_value=[model_item("llama-3.3-70b-versatile"), model_item("qwen/qwen3-32b")]):
            settings.action_chatbot_fallback_sync_models()
        self.assertTrue(self.env["chatbot.llm.model"]._find("groq", "qwen/qwen3-32b"))
        self.assertNotEqual(self.ICP.get_param("chatbot_assistant.fallback_active"), "True")
        self.assertFalse(self.ICP.get_param("chatbot_assistant.fallback_api_key"))

    def test_tarea_semanal_actualiza_el_catalogo_del_respaldo(self):
        self._activate()
        calls = []

        def fake_list(config):
            calls.append(config["provider"])
            return [model_item("gemini-2.5-flash")] if config["provider"] == "gemini" else [model_item("qwen/qwen3-32b")]
        with patch(LIST_MODELS, side_effect=fake_list):
            self.env["chatbot.llm.model"]._cron_sync_models()
        self.assertEqual(calls, ["gemini", "groq"])
        self.assertTrue(self.env["chatbot.llm.model"]._find("groq", "qwen/qwen3-32b"))


@tagged("post_install", "-at_install", "chatbot_assistant")
class TestSaveWithOneWorkingModel(FallbackSettingsCase):
    """Al guardar basta con que responda uno de los dos modelos, salvo errores de configuración."""

    def setUp(self):
        super().setUp()
        self.env["chatbot.llm.model"]._sync_provider("gemini", [model_item("gemini-2.5-flash"),
                                                                model_item("gemini-2.5-flash-lite")])
        self.flash_lite = self.env["chatbot.llm.model"]._find("gemini", "gemini-2.5-flash-lite")

    def _down(self, *down_models, code="server"):
        def connection(config):
            if config["model"] in down_models:
                raise LLMClientError(code)
            return connection_ok(config)
        return connection

    def test_principal_caido_se_guarda_si_el_respaldo_responde(self):
        self._activate()
        mocked = self._save({"chatbot_llm_model_id": self.flash_lite.id}, self._down("gemini-2.5-flash-lite"))
        self.assertEqual(mocked.call_count, 2, "se prueba el principal y, al fallar, el respaldo")
        self.assertEqual(self.ICP.get_param("chatbot_assistant.model"), "gemini-2.5-flash-lite")
        self.assertIn("No se pudo verificar", self.ICP.get_param("chatbot_assistant.last_verified"))

    def test_respaldo_caido_al_activarlo_se_guarda_si_el_principal_responde(self):
        mocked = self._save({"chatbot_fallback_active": True, "chatbot_fallback_provider": "groq",
                             "chatbot_fallback_api_key": "gsk_RESPALDO",
                             "chatbot_fallback_llm_model_id": self.groq_llama.id},
                            self._down("llama-3.3-70b-versatile", code="timeout"))
        self.assertEqual(mocked.call_count, 2)
        self.assertEqual(self.ICP.get_param("chatbot_assistant.fallback_active"), "True")
        self.assertIn("No se pudo verificar", self.ICP.get_param("chatbot_assistant.fallback_last_verified"))

    def test_sin_respaldo_si_el_principal_no_responde_no_se_guarda(self):
        with self.assertRaisesRegex(UserError, "ningún modelo respondió"):
            self._save({"chatbot_llm_model_id": self.flash_lite.id}, self._down("gemini-2.5-flash-lite"))
        self.assertEqual(self.ICP.get_param("chatbot_assistant.model"), "gemini-2.5-flash")

    def test_si_ninguno_responde_no_se_guarda(self):
        self._activate()
        with self.assertRaisesRegex(UserError, "ningún modelo respondió"):
            self._save({"chatbot_llm_model_id": self.flash_lite.id},
                       self._down("gemini-2.5-flash-lite", "llama-3.3-70b-versatile"))
        self.assertEqual(self.ICP.get_param("chatbot_assistant.model"), "gemini-2.5-flash")

    def test_clave_invalida_no_se_guarda_aunque_el_otro_responda(self):
        self._activate()
        with self.assertRaisesRegex(UserError, "(?s)la prueba de conexión falló.*API Key inválida"):
            self._save({"chatbot_llm_model_id": self.flash_lite.id},
                       self._down("gemini-2.5-flash-lite", code="auth"))
        self.assertEqual(self.ICP.get_param("chatbot_assistant.model"), "gemini-2.5-flash")
