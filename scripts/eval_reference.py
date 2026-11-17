# -*- coding: utf-8 -*-
"""
Referencia independiente para la evaluación del chatbot.

Calcula los datos correctos de cada consulta del dataset con consultas directas al ORM y campos
nativos de Odoo (por ejemplo `qty_available`), sin usar las funciones internas del asistente.
Así la evaluación no compara al asistente consigo mismo.

`facts(env, item, today)` retorna {ruta_en_los_datos_del_handler: valor_esperado}.
`compare(expected, data)` compara esos valores con los datos que devolvió el asistente.
"""
import calendar
from datetime import date

TOLERANCE = 0.01  # centavos / unidades con decimales


def _period(item, today):
    """Periodo esperado de la consulta: este mes, este año o sin filtro."""
    period = item.get("expected_period")
    if period == "this_month":
        last = calendar.monthrange(today.year, today.month)[1]
        return date(today.year, today.month, 1), date(today.year, today.month, last)
    if period == "this_year":
        return date(today.year, 1, 1), today
    return None, None


def _one(records, label):
    if len(records) != 1:
        raise ValueError("La referencia de %s no es única: %s" % (label, records.mapped("display_name")))
    return records


def _partner(env, name):
    partners = env["res.partner"].search([("name", "=ilike", name)])
    if not partners:
        partners = env["res.partner"].search([("name", "ilike", name), ("customer_rank", ">", 0)])
    return _one(partners, name)


def _product(env, entities):
    Product = env["product.product"]
    if entities.get("product_code"):
        return _one(Product.search([("default_code", "=ilike", entities["product_code"])]), entities["product_code"])
    name = entities["product_name"]
    products = Product.search([("name", "=ilike", name)]) or Product.search([("name", "ilike", name)])
    return _one(products, name)


def _confirmed_orders(env, partner):
    return env["sale.order"].search([("partner_id", "=", partner.id), ("state", "in", ("sale", "done"))])


def facts(env, item, today=None):
    today = today or date.today()
    intent = item["expected_intent"]
    entities = item.get("expected_entities") or {}

    if intent == "consultar_factura":
        if entities.get("invoice_number"):
            move = _one(env["account.move"].search([
                ("move_type", "=", "out_invoice"), ("name", "=", entities["invoice_number"]),
            ]), entities["invoice_number"])
            return {
                "invoices.0.name": move.name,
                "invoices.0.payment_state": move.payment_state,
                "invoices.0.amount_total": move.amount_total,
            }
        partner = _partner(env, entities["customer_name"])
        count = env["account.move"].search_count([
            ("move_type", "=", "out_invoice"), ("state", "=", "posted"), ("partner_id", "=", partner.id),
        ])
        return {"invoice_count": count}

    if intent == "consultar_stock":
        product = _product(env, entities)
        return {"product_code": product.default_code, "qty_on_hand": product.qty_available, "qty_free": product.free_qty}

    if intent == "consultar_ventas_cliente":
        if entities.get("product_code") or entities.get("product_name"):
            product = _product(env, entities)
            lines = env["sale.order.line"].search([
                ("product_id", "=", product.id), ("order_id.state", "in", ("sale", "done")),
            ])
            return {"product_code": product.default_code, "quantity": sum(lines.mapped("product_uom_qty"))}
        orders = _confirmed_orders(env, _partner(env, entities["customer_name"]))
        return {"order_count": len(orders), "amount_total": sum(orders.mapped("amount_total"))}

    if intent == "consultar_vendedor_cliente":
        partner = _partner(env, entities["customer_name"])
        return {"partner": partner.name, "salesperson": partner.user_id.name or None}

    if intent == "consultar_stock_facturacion_producto":
        product = _product(env, entities)
        date_from, date_to = _period(item, today)
        domain = [
            ("product_id", "=", product.id), ("display_type", "=", "product"),
            ("move_id.move_type", "=", "out_invoice"), ("move_id.state", "=", "posted"),
        ]
        if date_from:
            domain += [("move_id.invoice_date", ">=", date_from), ("move_id.invoice_date", "<=", date_to)]
        lines = env["account.move.line"].search(domain)
        return {
            "product_code": product.default_code,
            "qty_on_hand": product.qty_available,
            "qty_invoiced": sum(lines.mapped("quantity")),
            "invoice_count": len(lines.mapped("move_id")),
        }

    return {}


def _get(data, path):
    value = data
    for part in path.split("."):
        if isinstance(value, list):
            index = int(part)
            if index >= len(value):
                return None
            value = value[index]
        elif isinstance(value, dict):
            value = value.get(part)
        else:
            return None
    return value


def compare(expected, data):
    """Lista de diferencias entre los datos esperados y los que devolvió el asistente."""
    diffs = []
    for path, want in expected.items():
        got = _get(data or {}, path)
        if isinstance(want, (int, float)) and not isinstance(want, bool):
            ok = isinstance(got, (int, float)) and abs(float(got) - float(want)) <= TOLERANCE
        else:
            ok = got == want
        if not ok:
            diffs.append({"campo": path, "esperado": want, "obtenido": got})
    return diffs
