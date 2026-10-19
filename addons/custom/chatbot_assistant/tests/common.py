# -*- coding: utf-8 -*-
"""Datos de prueba propios: no dependen del módulo chatbot_test_data."""
from odoo import Command
from odoo.tests.common import TransactionCase, new_test_user

from ..services.prompt_builder import ENTITY_KEYS


def entities(**values):
    return {key: values.get(key) for key in ENTITY_KEYS}


class ChatbotCase(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.tester = new_test_user(
            cls.env, login="chatbot.tester",
            groups="base.group_user,sales_team.group_sale_salesman_all_leads,"
                   "stock.group_stock_user,account.group_account_invoice",
        )
        cls.salesperson = new_test_user(
            cls.env, login="vendedor.prueba@example.com", name="Vendedor Prueba",
            groups="base.group_user,sales_team.group_sale_salesman",
        )
        cls.salesperson.partner_id.phone = "0999999999"

        Partner = cls.env["res.partner"]
        cls.customer = Partner.create({
            "name": "Cliente Prueba Uno", "customer_rank": 1, "user_id": cls.salesperson.id,
        })
        cls.customer_two = Partner.create({"name": "Cliente Prueba Dos", "customer_rank": 1})
        Partner.create({"name": "Distribuidora Similar Norte", "customer_rank": 1})
        Partner.create({"name": "Distribuidora Similar Sur", "customer_rank": 1})

        Product = cls.env["product.product"]
        cls.product = Product.create({
            "name": "Producto Prueba Filtro", "default_code": "TST-001", "type": "consu",
            "is_storable": True, "list_price": 100.0, "taxes_id": [Command.clear()],
        })
        cls.product_other = Product.create({
            "name": "Producto Prueba Casco", "default_code": "TST-002", "type": "consu",
            "is_storable": True, "list_price": 50.0, "taxes_id": [Command.clear()],
        })

        warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        cls.stock_location = warehouse.lot_stock_id
        cls.env["stock.quant"]._update_available_quantity(cls.product, cls.stock_location, 50.0)

        # 17 pedidos confirmados (más que el límite de 15 del listado); cada uno reserva 1 unidad.
        cls.orders = cls.env["sale.order"]
        for _i in range(17):
            order = cls.env["sale.order"].create({
                "partner_id": cls.customer.id,
                "order_line": [Command.create({
                    "product_id": cls.product.id, "product_uom_qty": 1, "price_unit": 100.0,
                    "tax_id": [Command.clear()],
                })],
            })
            order.action_confirm()
            cls.orders |= order
        # action_confirm fija date_order a "ahora"; se reasignan fechas conocidas.
        cls.orders.write({"date_order": "2026-06-10 10:00:00"})
        cls.order_last_day = cls.orders[0]
        cls.order_last_day.date_order = "2026-07-31 15:30:00"

        cls.invoice_july = cls._create_invoice(cls.customer, "2026-07-15", 3)
        cls.invoice_august = cls._create_invoice(cls.customer, "2026-08-10", 2)
        cls.invoice_draft = cls._create_invoice(cls.customer, "2026-07-20", 100, post=False)

    @classmethod
    def _create_invoice(cls, partner, invoice_date, quantity, post=True):
        move = cls.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": partner.id,
            "invoice_date": invoice_date,
            "invoice_line_ids": [Command.create({
                "product_id": cls.product.id, "quantity": quantity, "price_unit": 10.0,
                "tax_ids": [Command.clear()],
            })],
        })
        if post:
            move.action_post()
        return move
