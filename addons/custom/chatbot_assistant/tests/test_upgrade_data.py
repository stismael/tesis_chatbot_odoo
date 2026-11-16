# -*- coding: utf-8 -*-
"""
Actualizar el módulo no debe fallar si el administrador borró y volvió a crear un dato inicial
(fila de permisos, modelo del catálogo o parámetro). Antes, la actualización recreaba el registro
borrado y chocaba con la restricción de clave única.
"""
from odoo.tests import TransactionCase, tagged
from odoo.tools.convert import convert_file


@tagged("post_install", "-at_install", "chatbot_assistant")
class TestUpgradeData(TransactionCase):

    def _reload(self, filename):
        convert_file(self.env, "chatbot_assistant", filename, {}, mode="update", noupdate=True)

    def test_permiso_borrado_y_recreado(self):
        row = self.env.ref("chatbot_assistant.permission_consultar_stock")
        values = {"intent": row.intent, "area_label": row.area_label, "group_ids": [(6, 0, row.group_ids.ids)]}
        row.unlink()
        new_row = self.env["chatbot.intent.permission"].create(values)
        self._reload("data/chatbot_intent_permission_data.xml")
        rows = self.env["chatbot.intent.permission"].search([("intent", "=", "consultar_stock")])
        self.assertEqual(rows, new_row)

    def test_modelo_del_catalogo_borrado_y_sincronizado(self):
        self.env.ref("chatbot_assistant.llm_model_gemini_25_flash").unlink()
        self.env["chatbot.llm.model"]._sync_provider("gemini", [{"id": "gemini-2.5-flash"}])
        self._reload("data/chatbot_llm_model_data.xml")
        found = self.env["chatbot.llm.model"].search([("provider", "=", "gemini"), ("model_id", "=", "gemini-2.5-flash")])
        self.assertEqual(len(found), 1)

    def test_parametro_borrado_y_recreado(self):
        ICP = self.env["ir.config_parameter"].sudo()
        ICP.search([("key", "=", "chatbot_assistant.provider")]).unlink()
        ICP.set_param("chatbot_assistant.provider", "groq")
        self._reload("data/default_params.xml")
        self.assertEqual(ICP.get_param("chatbot_assistant.provider"), "groq")
        self.assertEqual(ICP.search_count([("key", "=", "chatbot_assistant.provider")]), 1)
