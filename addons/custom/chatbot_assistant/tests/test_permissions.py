# -*- coding: utf-8 -*-
from unittest.mock import patch

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from ..services.handlers.access import SCOPE_NOTE
from ..services.help_text import build_help_markup
from .common import ChatbotCase
from .test_orchestrator_security import COMPLETE_JSON, llm_output

QUERIES = {
    "consultar_factura": llm_output("consultar_factura", customer_name="Cliente Prueba Uno"),
    "consultar_stock": llm_output("consultar_stock", product_code="TST-001"),
    "consultar_ventas_cliente": llm_output("consultar_ventas_cliente", customer_name="Cliente Prueba Uno"),
    "consultar_vendedor_cliente": llm_output("consultar_vendedor_cliente", customer_name="Cliente Prueba Uno"),
    "consultar_stock_facturacion_producto": llm_output(
        "consultar_stock_facturacion_producto", product_code="TST-001"),
}


@tagged("post_install", "-at_install", "chatbot_assistant")
class TestIntentPermissions(ChatbotCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.profiles = {
            "sin_grupos": new_test_user(cls.env, login="perfil.sin.grupos", groups="base.group_user"),
            "inventario": new_test_user(
                cls.env, login="perfil.inventario", groups="base.group_user,stock.group_stock_user"),
            "vendedor_propio": new_test_user(
                cls.env, login="perfil.vendedor", groups="base.group_user,sales_team.group_sale_salesman"),
            "facturacion": new_test_user(
                cls.env, login="perfil.facturacion", groups="base.group_user,account.group_account_invoice"),
            "admin_inventario": new_test_user(
                cls.env, login="perfil.admin.inventario", groups="base.group_user,stock.group_stock_manager"),
        }

    def setUp(self):
        super().setUp()
        self.env["ir.config_parameter"].sudo().set_param("chatbot_assistant.api_key", "clave-de-prueba")

    def _ask(self, user, intent, output=None):
        user_env = self.env(user=user)
        session = user_env["chatbot.session"].create({"name": "permisos"})
        with patch(COMPLETE_JSON, return_value=output or QUERIES[intent]):
            result = user_env["chatbot.orchestrator"].evaluate_query(intent, session=session)
        return result, self.env["chatbot.query.log"].browse(result["log_id"])

    def _assert_allowed(self, user, intent):
        result, log = self._ask(user, intent)
        self.assertNotEqual(log.outcome, "forbidden", f"{user.login} debería poder: {intent} → {result['reply']}")
        return result

    def _assert_forbidden(self, user, intent, area):
        result, log = self._ask(user, intent)
        self.assertEqual((log.outcome, log.error_code), ("forbidden", "intent_permission"), user.login)
        self.assertEqual(result["reply"], f"No tienes permiso para consultar {area}. Pide acceso al administrador.")
        self.assertFalse(result["data"], "No debe consultarse nada sin permiso")
        return result

    # Matriz de permisos por perfil --------------------------------------------

    def test_usuario_sin_grupos_no_consulta_nada(self):
        user = self.profiles["sin_grupos"]
        self._assert_forbidden(user, "consultar_factura", "facturas")
        self._assert_forbidden(user, "consultar_stock", "inventario")
        self._assert_forbidden(user, "consultar_ventas_cliente", "ventas")
        self._assert_forbidden(user, "consultar_vendedor_cliente", "el vendedor asignado a un cliente")
        self._assert_forbidden(user, "consultar_stock_facturacion_producto", "inventario y facturación")

    def test_solo_inventario(self):
        user = self.profiles["inventario"]
        result = self._assert_allowed(user, "consultar_stock")
        self.assertIn("en existencia", result["reply"])
        self._assert_forbidden(user, "consultar_factura", "facturas")
        self._assert_forbidden(user, "consultar_stock_facturacion_producto", "inventario y facturación")

    def test_administrador_del_modulo_incluye_al_usuario(self):
        self._assert_allowed(self.profiles["admin_inventario"], "consultar_stock")

    def test_solo_facturacion(self):
        user = self.profiles["facturacion"]
        self._assert_allowed(user, "consultar_factura")
        self._assert_forbidden(user, "consultar_stock", "inventario")

    def test_vendedor_ve_solo_sus_pedidos_con_aviso(self):
        user = self.profiles["vendedor_propio"]
        self.orders[:3].user_id = user
        result = self._assert_allowed(user, "consultar_ventas_cliente")
        self.assertEqual(result["data"]["order_count"], 3)
        self.assertIn(SCOPE_NOTE.strip(), result["reply"])
        self._assert_forbidden(user, "consultar_factura", "facturas")

    def test_acceso_total_sin_aviso(self):
        result = self._assert_allowed(self.tester, "consultar_ventas_cliente")
        self.assertEqual(result["data"]["order_count"], 17)
        self.assertNotIn(SCOPE_NOTE.strip(), result["reply"])

    def test_administrador_puede_todo(self):
        admin = self.env.ref("base.user_admin")
        for intent in QUERIES:
            self._assert_allowed(admin, intent)

    def test_permiso_se_revisa_antes_de_pedir_datos(self):
        output = llm_output("consultar_stock", "missing_information", ["product_name"])
        result, log = self._ask(self.profiles["sin_grupos"], "consultar_stock", output)
        self.assertEqual(log.outcome, "forbidden")
        self.assertNotIn("indique", result["reply"].lower())

    # Tabla editable ----------------------------------------------------------

    def test_fila_sin_grupos_usa_solo_los_permisos_de_odoo(self):
        self.env.ref("chatbot_assistant.permission_consultar_stock").group_ids = [(5, 0, 0)]
        # Odoo permite a todo usuario interno leer existencias.
        result = self._assert_allowed(self.profiles["sin_grupos"], "consultar_stock")
        self.assertIn("en existencia", result["reply"])

    def test_fila_sin_grupos_y_odoo_niega(self):
        self.env.ref("chatbot_assistant.permission_consultar_factura").group_ids = [(5, 0, 0)]
        result, log = self._ask(self.profiles["sin_grupos"], "consultar_factura")
        self.assertEqual((log.outcome, log.error_code), ("forbidden", "access"))
        self.assertNotIn("not allowed", result["reply"])

    def test_el_administrador_puede_agregar_grupos(self):
        row = self.env.ref("chatbot_assistant.permission_consultar_stock")
        row.group_ids = [(4, self.env.ref("sales_team.group_sale_salesman").id)]
        self._assert_forbidden(self.profiles["inventario"], "consultar_stock", "inventario")

    def test_solo_el_administrador_del_chatbot_edita_la_tabla(self):
        row = self.env.ref("chatbot_assistant.permission_consultar_stock")
        with self.assertRaises(AccessError):
            row.with_user(self.tester).write({"area_label": "otro"})
        row.with_user(self.env.ref("base.user_admin")).write({"area_label": "existencias"})
        self.assertEqual(row.area_label, "existencias")

    # Ayuda filtrada ----------------------------------------------------------

    def test_ayuda_muestra_solo_lo_permitido(self):
        Permission = self.env["chatbot.intent.permission"]
        allowed = Permission._allowed_intents(self.profiles["inventario"])
        self.assertEqual(allowed, ["consultar_stock"])
        html = build_help_markup(allowed)
        self.assertIn("Inventario", html)
        self.assertNotIn("Facturas", html)
        self.assertIn("no puedes hacer consultas", build_help_markup([]))
