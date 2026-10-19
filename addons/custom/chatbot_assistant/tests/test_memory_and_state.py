# -*- coding: utf-8 -*-
from unittest.mock import patch

from odoo import Command
from odoo.tests import tagged

from .common import ChatbotCase
from .test_orchestrator_security import COMPLETE_JSON, llm_output

JULY_2020 = {"date_from": "2020-07-01", "date_to": "2020-07-31"}


@tagged("post_install", "-at_install", "chatbot_assistant")
class TestSessionMemory(ChatbotCase):

    def setUp(self):
        super().setUp()
        self.env["ir.config_parameter"].sudo().set_param("chatbot_assistant.api_key", "clave-de-prueba")
        self.user_env = self.env(user=self.tester)
        self.session = self.user_env["chatbot.session"].create({"name": "memoria"})

    def _ask(self, output, text="consulta"):
        with patch(COMPLETE_JSON, return_value=output):
            return self.user_env["chatbot.orchestrator"].evaluate_query(text, session=self.session)

    def test_seguimiento_no_arrastra_las_fechas(self):
        self._ask(llm_output("consultar_stock_facturacion_producto", product_code="TST-001", **JULY_2020))
        # "¿Y cuántas ventas hay de este producto?": hereda el producto, no el periodo de julio de 2020.
        result = self._ask(llm_output("consultar_ventas_cliente", "missing_information", ["product_name"]))
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["data"]["product_code"], "TST-001")
        self.assertEqual(result["data"]["order_count"], 17)

    def test_cambio_de_tema_descarta_lo_pendiente(self):
        self._ask(llm_output("consultar_ventas_cliente", "missing_information", ["customer_name"], **JULY_2020))
        self.assertEqual(self.session.pending_intent, "consultar_ventas_cliente")
        self._ask(llm_output("consultar_stock", product_code="TST-001"))
        memory = self.session.get_pending_entities()
        self.assertFalse(memory.get("date_from"), "Las fechas de la pregunta abandonada no quedan en memoria")
        self.assertEqual(memory.get("product_code"), "TST-001")

        result = self._ask(llm_output("consultar_ventas_cliente", "missing_information", ["product_name"]))
        self.assertEqual(result["data"]["order_count"], 17)

    def test_la_aclaracion_conserva_lo_ya_dicho(self):
        self._ask(llm_output("consultar_ventas_cliente", "missing_information", ["customer_name"], **JULY_2020))
        # El usuario responde solo el producto: se conserva el periodo pedido antes.
        result = self._ask(llm_output("consultar_ventas_cliente", product_code="TST-001"))
        self.assertIn("No hay pedidos confirmados de TST-001", result["reply"])
        self.assertFalse(self.session.pending_intent)

    def test_respuesta_corta_completa_la_consulta_pendiente(self):
        self._ask(llm_output("consultar_stock", "missing_information", ["product_name"], location_name="Stock"))
        result = self._ask(llm_output("consultar_vendedor_cliente", "missing_information", ["customer_name"]))
        # La IA no reconoció la intención, pero el mensaje no aporta datos: sigue la consulta pendiente.
        self.assertEqual(result["intent"], "consultar_stock")
        self.assertEqual(result["status"], "missing_information")


@tagged("post_install", "-at_install", "chatbot_assistant")
class TestOrderState(ChatbotCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        line = [Command.create({
            "product_id": cls.product.id, "product_uom_qty": 4, "price_unit": 100.0, "tax_id": [Command.clear()],
        })]
        SaleOrder = cls.env["sale.order"]
        cls.quotations = SaleOrder.create([
            {"partner_id": cls.customer.id, "order_line": line},
            {"partner_id": cls.customer.id, "order_line": line},
        ])
        cls.cancelled = SaleOrder.create({"partner_id": cls.customer.id, "order_line": line})
        cls.cancelled.action_cancel()

    def setUp(self):
        super().setUp()
        self.env["ir.config_parameter"].sudo().set_param("chatbot_assistant.api_key", "clave-de-prueba")

    def _ask(self, **entities):
        session = self.env["chatbot.session"].create({"name": "estado"})
        with patch(COMPLETE_JSON, return_value=llm_output("consultar_ventas_cliente", **entities)):
            return self.env["chatbot.orchestrator"].evaluate_query("ventas", session=session)

    def test_sin_estado_cuenta_los_pedidos_confirmados(self):
        result = self._ask(customer_name="Cliente Prueba Uno")
        self.assertIn("17 pedido(s) confirmado(s)", result["reply"])

    def test_cotizaciones(self):
        result = self._ask(customer_name="Cliente Prueba Uno", order_state="cotizacion")
        self.assertIn("2 cotización(es)", result["reply"])
        self.assertEqual(result["data"]["order_count"], 2)
        result = self._ask(product_code="TST-001", order_state="cotizacion")
        self.assertIn("8 unidades cotizadas en 2 cotización(es)", result["reply"])

    def test_cancelados(self):
        result = self._ask(customer_name="Cliente Prueba Uno", order_state="cancelado")
        self.assertIn("1 pedido(s) cancelado(s)", result["reply"])
        result = self._ask(customer_name="Cliente Prueba Dos", order_state="cancelado")
        self.assertIn("No hay pedidos cancelados", result["reply"])
