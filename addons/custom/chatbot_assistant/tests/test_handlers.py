# -*- coding: utf-8 -*-
from odoo.tests import tagged

from ..services.handlers import HANDLER_MAP
from .common import ChatbotCase, entities


@tagged("post_install", "-at_install", "chatbot_assistant")
class TestHandlers(ChatbotCase):

    def _run(self, intent, user_text="", **values):
        """Ejecuta el handler como un usuario interno normal (respeta permisos de Odoo)."""
        return HANDLER_MAP[intent](self.env(user=self.tester), entities(**values), user_text=user_text)

    # CU-01 -----------------------------------------------------------------

    def test_factura_por_numero(self):
        result = self._run("consultar_factura", invoice_number=self.invoice_july.name)
        self.assertTrue(result["ok"])
        self.assertIn(self.invoice_july.name, result["message"])
        self.assertIn("no pagada", result["message"])

    def test_factura_por_cliente_con_periodo(self):
        result = self._run(
            "consultar_factura", customer_name="Cliente Prueba Uno",
            date_from="2026-07-01", date_to="2026-07-31",
        )
        self.assertTrue(result["ok"])
        names = [row["name"] for row in result["data"]["invoices"]]
        self.assertEqual(names, [self.invoice_july.name])

    def test_factura_borrador_no_se_consulta(self):
        result = self._run("consultar_factura", customer_name="Cliente Prueba Uno")
        names = [row["name"] for row in result["data"]["invoices"]]
        self.assertNotIn(self.invoice_draft.name, names)

    # CU-02 -----------------------------------------------------------------

    def test_stock_existencia_reservado_y_libre(self):
        result = self._run("consultar_stock", product_code="TST-001")
        data = result["data"]
        self.assertEqual(data["qty_on_hand"], 50)
        self.assertEqual(data["qty_reserved"], 17)
        self.assertEqual(data["qty_free"], 33)
        # Mismo criterio que los campos nativos de Odoo
        self.assertEqual(data["qty_on_hand"], self.product.qty_available)
        self.assertEqual(data["qty_free"], self.product.free_qty)
        self.assertIn("17 reservadas para pedidos", result["message"])

    def test_stock_con_ubicacion_usa_el_mismo_criterio(self):
        general = self._run("consultar_stock", product_code="TST-001")["data"]
        by_location = self._run(
            "consultar_stock", product_code="TST-001", location_name=self.stock_location.complete_name,
        )["data"]
        self.assertEqual(general["qty_on_hand"], by_location["qty_on_hand"])
        self.assertEqual(general["qty_free"], by_location["qty_free"])

    def test_stock_ubicacion_inexistente(self):
        result = self._run("consultar_stock", product_code="TST-001", location_name="NO-EXISTE")
        self.assertFalse(result["ok"])
        self.assertIn("ubicación", result["message"])

    def test_stock_producto_ambiguo(self):
        result = self._run("consultar_stock", product_name="Producto Prueba")
        self.assertEqual(result.get("status"), "ambiguous")

    # CU-03 -----------------------------------------------------------------

    def test_ventas_cliente_cuenta_todos_los_pedidos(self):
        result = self._run("consultar_ventas_cliente", customer_name="Cliente Prueba Uno")
        self.assertEqual(result["data"]["order_count"], 17)
        self.assertAlmostEqual(result["data"]["amount_total"], 1700.0)
        self.assertIn("17 pedido(s)", result["message"])

    def test_ventas_listado_indica_que_muestra_solo_15(self):
        result = self._run(
            "consultar_ventas_cliente", user_text="lista los pedidos", customer_name="Cliente Prueba Uno",
        )
        self.assertIn("se muestran los 15 más recientes", result["message"])
        self.assertEqual(result["message"].count("\n- "), 15)

    def test_ventas_fecha_final_incluye_todo_el_dia(self):
        # date_order es fecha y hora; Odoo amplía "<= AAAA-MM-DD" hasta el final de ese día.
        result = self._run(
            "consultar_ventas_cliente", customer_name="Cliente Prueba Uno",
            date_from="2026-07-31", date_to="2026-07-31",
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["order_count"], 1)

    def test_ventas_por_producto(self):
        result = self._run("consultar_ventas_cliente", product_code="TST-001")
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["quantity"], 17)

    def test_ventas_cliente_ambiguo(self):
        result = self._run("consultar_ventas_cliente", customer_name="Distribuidora Similar")
        self.assertEqual(result.get("status"), "ambiguous")

    # CU-04 -----------------------------------------------------------------

    def test_vendedor_asignado(self):
        result = self._run("consultar_vendedor_cliente", customer_name="Cliente Prueba Uno")
        self.assertTrue(result["ok"])
        self.assertIn("Vendedor Prueba", result["message"])
        self.assertIn("0999999999", result["message"])

    def test_cliente_sin_vendedor(self):
        result = self._run("consultar_vendedor_cliente", customer_name="Cliente Prueba Dos")
        self.assertFalse(result["ok"])
        self.assertIn("no tiene vendedor asignado", result["message"])

    # CU-05 -----------------------------------------------------------------

    def test_stock_facturacion_sin_periodo(self):
        data = self._run("consultar_stock_facturacion_producto", product_code="TST-001")["data"]
        self.assertEqual(data["qty_invoiced"], 5)          # 3 + 2; el borrador no cuenta
        self.assertEqual(data["invoice_count"], 2)
        self.assertAlmostEqual(data["amount_invoiced"], 50.0)
        self.assertEqual(data["qty_on_hand"], 50)
        self.assertEqual(data["qty_free"], 33)

    def test_stock_facturacion_con_periodo(self):
        data = self._run(
            "consultar_stock_facturacion_producto", product_code="TST-001",
            date_from="2026-07-01", date_to="2026-07-31",
        )["data"]
        self.assertEqual(data["qty_invoiced"], 3)
        self.assertEqual(data["invoice_count"], 1)

    def test_stock_facturacion_periodo_sin_facturas(self):
        result = self._run(
            "consultar_stock_facturacion_producto", product_code="TST-002",
            date_from="2026-07-01", date_to="2026-07-31",
        )
        self.assertTrue(result["ok"])
        self.assertIn("No hay facturas de cliente publicadas", result["message"])
