# -*- coding: utf-8 -*-
"""Resultados extensos: vista previa en el chat, «Ver todo» y descarga en CSV."""
import json
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import HttpCase, tagged
from odoo.tests.common import new_test_user

from ..services.handlers import HANDLER_MAP
from ..services.result_set import PREVIEW_ROWS, build_csv
from .common import ChatbotCase, entities

COMPLETE_JSON = "odoo.addons.chatbot_assistant.services.llm_client.complete_json"


def llm_output(intent, **values):
    return {"intent": intent, "entities": entities(**values), "status": "ready", "missing_entities": []}


@tagged("post_install", "-at_install", "chatbot_assistant")
class TestLongResults(ChatbotCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # 7 facturas publicadas más (9 en total): más que la vista previa de 5.
        cls.more_invoices = cls.env["account.move"]
        for day in range(1, 8):
            cls.more_invoices |= cls._create_invoice(cls.customer, "2026-09-%02d" % day, 1)
        cls.env["ir.config_parameter"].sudo().set_param("chatbot_assistant.api_key", "clave-de-prueba")

    def setUp(self):
        super().setUp()
        self.user_env = self.env(user=self.tester)
        self.session = self.user_env["chatbot.session"].create({"name": "prueba"})

    def _run(self, intent, user_text="", **values):
        return HANDLER_MAP[intent](self.user_env, entities(**values), user_text=user_text)

    def _ask(self, text, output):
        with patch(COMPLETE_JSON, return_value=output):
            return self.user_env["chatbot.orchestrator"].evaluate_query(text, session=self.session)

    # Vista previa en los handlers ----------------------------------------------------------

    def test_facturas_por_cliente_vista_previa_y_totales(self):
        result = self._run("consultar_factura", customer_name="Cliente Prueba Uno")
        message = result["message"]
        self.assertIn('Facturas de "Cliente Prueba Uno": 9', message)
        self.assertIn("saldo pendiente", message)
        self.assertEqual(message.count("\n- "), PREVIEW_ROWS)
        self.assertIn("Mostrando 5 de 9 facturas", message)
        self.assertEqual(result["data"]["invoice_count"], 9)
        records = result["records"]
        self.assertEqual(records["model"], "account.move")
        self.assertEqual(len(records["ids"]), 9)
        # La vista previa son las más recientes.
        self.assertIn(self.more_invoices[-1].name, message)

    def test_pocas_facturas_no_ofrecen_ver_todo(self):
        result = self._run(
            "consultar_factura", customer_name="Cliente Prueba Uno",
            date_from="2026-07-01", date_to="2026-08-31",
        )
        self.assertNotIn("Mostrando", result["message"])
        self.assertFalse(result.get("records"))

    def test_ventas_cliente_resumen_ofrece_todos_los_pedidos(self):
        result = self._run("consultar_ventas_cliente", customer_name="Cliente Prueba Uno")
        self.assertIn("17 pedido(s)", result["message"])
        self.assertNotIn("pídeme que los liste", result["message"])
        self.assertEqual(result["records"]["model"], "sale.order")
        self.assertEqual(sorted(result["records"]["ids"]), sorted(self.orders.ids))

    def test_ventas_por_producto_lista_con_vista_previa(self):
        result = self._run("consultar_ventas_cliente", user_text="lista los pedidos", product_code="TST-001")
        self.assertIn("Pedidos con TST-001", result["message"])
        self.assertIn("Mostrando 5 de 17 líneas de pedido", result["message"])
        self.assertEqual(result["message"].count("\n- "), PREVIEW_ROWS)
        self.assertEqual(result["records"]["model"], "sale.order.line")
        self.assertEqual(len(result["records"]["ids"]), 17)

    def test_stock_facturacion_ofrece_las_facturas(self):
        result = self._run("consultar_stock_facturacion_producto", product_code="TST-001")
        self.assertEqual(result["records"]["model"], "account.move")
        self.assertEqual(len(result["records"]["ids"]), result["data"]["invoice_count"])

    # Auditoría y mensaje en el chat --------------------------------------------------------

    def test_la_consulta_guarda_el_resultado_completo(self):
        result = self._ask(
            "facturas de Cliente Prueba Uno", llm_output("consultar_factura", customer_name="Cliente Prueba Uno"),
        )
        self.assertEqual(result["result_count"], 9)
        log = self.env["chatbot.query.log"].browse(result["log_id"])
        self.assertEqual(log.result_model, "account.move")
        self.assertEqual(len(json.loads(log.result_ids_json)), 9)
        self.assertEqual(log.result_title, "Facturas de Cliente Prueba Uno")

    def test_mensaje_con_ver_todo_y_csv(self):
        service = self.env["chatbot.discuss.service"]
        html = str(service._format_reply_html("Facturas", 42, 9))
        self.assertIn("action_chatbot_open_result?active_id=42", html)
        self.assertIn("Ver todo (9)", html)
        self.assertIn("/chatbot_assistant/resultado/42/csv", html)
        # Pocos registros: «Ver todo» sin CSV; sin resultado: sin enlaces.
        self.assertNotIn("csv", str(service._format_reply_html("Facturas", 42, 3)))
        self.assertNotIn("<a", str(service._format_reply_html("Hola", 42, 0)))

    def test_mensaje_en_discuss_lleva_los_enlaces(self):
        bot = self.env.ref("chatbot_assistant.partner_chatbot_assistant")
        channel = self.user_env["discuss.channel"].channel_get([bot.id])
        with patch(COMPLETE_JSON, return_value=llm_output("consultar_factura", customer_name="Cliente Prueba Uno")):
            channel.message_post(body="facturas de Cliente Prueba Uno", message_type="comment",
                                 subtype_xmlid="mail.mt_comment")
        reply = channel.message_ids.filtered(lambda m: m.author_id == bot)[:1]
        self.assertIn("Ver todo (9)", str(reply.body))
        self.assertIn("Descargar CSV", str(reply.body))

    # Ver todo ----------------------------------------------------------------------------

    def test_ver_todo_abre_la_lista_con_los_registros_exactos(self):
        result = self._ask(
            "facturas de Cliente Prueba Uno", llm_output("consultar_factura", customer_name="Cliente Prueba Uno"),
        )
        log = self.user_env["chatbot.query.log"].browse(result["log_id"])
        action = log.action_open_result()
        self.assertEqual(action["res_model"], "account.move")
        ids = action["domain"][0][2]
        self.assertEqual(len(ids), 9)
        self.assertEqual(log.sudo().result_views, 1)

    def test_otro_usuario_no_puede_abrir_el_resultado(self):
        result = self._ask(
            "facturas de Cliente Prueba Uno", llm_output("consultar_factura", customer_name="Cliente Prueba Uno"),
        )
        other = new_test_user(self.env, login="otro.usuario", groups="base.group_user,account.group_account_invoice")
        with self.assertRaisesRegex(UserError, "otro usuario"):
            self.env(user=other)["chatbot.query.log"].browse(result["log_id"]).action_open_result()

    def test_ver_todo_por_url_funciona_para_un_usuario_normal(self):
        """La acción del enlace la ejecuta un usuario sin permiso de escritura sobre la auditoría."""
        result = self._ask(
            "facturas de Cliente Prueba Uno", llm_output("consultar_factura", customer_name="Cliente Prueba Uno"),
        )
        self.assertFalse(self.user_env.user.has_group("chatbot_assistant.group_chatbot_manager"))
        server_action = self.env.ref("chatbot_assistant.action_chatbot_open_result")
        action = server_action.with_user(self.tester).with_context(active_id=result["log_id"]).run()
        self.assertEqual(action["res_model"], "account.move")
        self.assertEqual(len(action["domain"][0][2]), 9)

    def test_permisos_de_odoo_se_vuelven_a_aplicar(self):
        """Si el usuario solo ve sus documentos, «Ver todo» no muestra pedidos ajenos."""
        own_only = new_test_user(self.env, login="solo.propios", groups="base.group_user,sales_team.group_sale_salesman")
        mine = self.orders[0].copy({"user_id": own_only.id})
        log = self.env["chatbot.query.log"].sudo().create({
            "name": "x", "query": "x", "user_id": own_only.id, "result_model": "sale.order",
            "result_ids_json": json.dumps(self.orders.ids + mine.ids), "result_count": 18,
        })
        records = log.with_user(own_only)._result_records()
        self.assertEqual(records, mine.with_user(own_only))

    # CSV ---------------------------------------------------------------------------------

    def test_csv_tiene_solo_columnas_autorizadas(self):
        invoices = self.more_invoices.with_user(self.tester)
        content = build_csv(invoices).decode("utf-8-sig").splitlines()
        self.assertEqual(
            content[0], "Factura,Cliente,Fecha,Vencimiento,Total,Saldo pendiente,Estado de pago",
        )
        self.assertEqual(len(content), 1 + len(invoices))
        self.assertIn("Cliente Prueba Uno", content[1])
        self.assertIn("10.00", content[1])

    def test_csv_de_lineas_de_pedido(self):
        lines = self.orders.order_line.with_user(self.tester)
        content = build_csv(lines).decode("utf-8-sig").splitlines()
        self.assertTrue(content[0].startswith("Pedido,Cliente,Fecha,Producto,Cantidad"))
        self.assertEqual(len(content), 18)


@tagged("post_install", "-at_install", "chatbot_assistant")
class TestLongResultsHttp(HttpCase):
    """Descarga del CSV y apertura de «Ver todo» por URL, como lo hace el navegador."""

    def setUp(self):
        super().setUp()
        self.owner = new_test_user(
            self.env, login="dueno.csv", password="dueno.csv12345",
            groups="base.group_user,account.group_account_invoice",
        )
        self.other = new_test_user(
            self.env, login="otro.csv", password="otro.csv12345",
            groups="base.group_user,account.group_account_invoice",
        )
        partner = self.env["res.partner"].create({"name": "Cliente CSV"})
        self.invoices = self.env["account.move"]
        for day in range(1, 8):
            move = self.env["account.move"].create({
                "move_type": "out_invoice", "partner_id": partner.id, "invoice_date": "2026-09-%02d" % day,
                "invoice_line_ids": [(0, 0, {"name": "Servicio", "quantity": 1, "price_unit": 10.0, "tax_ids": [(5,)]})],
            })
            move.action_post()
            self.invoices |= move
        self.log = self.env["chatbot.query.log"].create({
            "name": "facturas", "query": "facturas", "user_id": self.owner.id,
            "result_model": "account.move", "result_ids_json": json.dumps(self.invoices.ids),
            "result_title": "Facturas de Cliente CSV", "result_count": 7,
        })

    def test_el_dueno_descarga_el_csv(self):
        self.authenticate("dueno.csv", "dueno.csv12345")
        response = self.url_open("/chatbot_assistant/resultado/%s/csv" % self.log.id)
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response.headers["Content-Type"])
        self.assertIn("Facturas_de_Cliente_CSV.csv", response.headers["Content-Disposition"])
        lines = response.content.decode("utf-8-sig").splitlines()
        self.assertEqual(len(lines), 8)
        self.log.invalidate_recordset()
        self.assertEqual(self.log.csv_downloads, 1)
        self.assertTrue(self.log.last_csv_download)

    def test_otro_usuario_recibe_404(self):
        self.authenticate("otro.csv", "otro.csv12345")
        response = self.url_open("/chatbot_assistant/resultado/%s/csv" % self.log.id)
        self.assertEqual(response.status_code, 404)
        self.log.invalidate_recordset()
        self.assertEqual(self.log.csv_downloads, 0)

    def test_sin_sesion_no_descarga(self):
        response = self.url_open("/chatbot_assistant/resultado/%s/csv" % self.log.id, allow_redirects=False)
        self.assertNotEqual(response.status_code, 200)

    def test_resultado_inexistente_da_404(self):
        self.authenticate("dueno.csv", "dueno.csv12345")
        response = self.url_open("/chatbot_assistant/resultado/999999/csv")
        self.assertEqual(response.status_code, 404)
