# -*- coding: utf-8 -*-
"""CU-05: consultar stock actual y facturación de un producto en un periodo."""

from .stock import available_qty
from .ventas import _find_product, _product_label


def _period_label(date_from, date_to):
    if date_from and date_to:
        return f"entre {date_from} y {date_to}"
    if date_from:
        return f"desde {date_from}"
    if date_to:
        return f"hasta {date_to}"
    return "en total (sin filtro de fechas)"


def _invoice_lines_domain(product, date_from=None, date_to=None):
    """Solo líneas de producto de facturas de cliente publicadas (sin impuestos, notas ni secciones)."""
    domain = [
        ("product_id", "=", product.id),
        ("display_type", "=", "product"),
        ("move_id.move_type", "=", "out_invoice"),
        ("move_id.state", "=", "posted"),
    ]
    if date_from:
        domain.append(("move_id.invoice_date", ">=", date_from))
    if date_to:
        domain.append(("move_id.invoice_date", "<=", date_to))
    return domain


def handle(env, entities, user_text=""):
    product_code = entities.get("product_code")
    product_name = entities.get("product_name")
    location_name = entities.get("location_name")
    date_from = entities.get("date_from")
    date_to = entities.get("date_to")

    if not (product_code or product_name):
        return {
            "ok": False,
            "message": "Indique el código o el nombre del producto.",
            "data": {},
        }

    products = _find_product(env, product_code=product_code, product_name=product_name)
    if not products:
        ref = product_code or product_name
        return {
            "ok": False,
            "message": f'No encontré un producto con la referencia "{ref}".',
            "data": {},
        }
    if len(products) > 1:
        names = ", ".join(products.mapped("display_name"))
        return {
            "ok": False,
            "status": "ambiguous",
            "message": f"Hay varios productos similares: {names}. Indique el código o nombre exacto.",
            "data": {"candidates": products.mapped("display_name")},
        }
    product = products[0]
    label = _product_label(product)

    qty = available_qty(env, product, location_name)
    if qty is None:
        return {
            "ok": False,
            "message": f'No encontré la ubicación "{location_name}".',
            "data": {},
        }

    lines = env["account.move.line"].search(_invoice_lines_domain(product, date_from, date_to))
    qty_invoiced = sum(lines.mapped("quantity"))
    amount_invoiced = sum(lines.mapped("price_subtotal"))
    invoices = lines.mapped("move_id")
    currency = lines[:1].currency_id or env.company.currency_id
    symbol = currency.symbol or currency.name or "USD"
    uom = product.uom_id.name or "Ud"
    period = _period_label(date_from, date_to)
    loc_msg = f' en la ubicación "{location_name}"' if location_name else " en ubicaciones internas"

    message = f"{label}: {qty:g} {uom} disponibles{loc_msg}. "
    if lines:
        message += (
            f"Facturado {period}: {qty_invoiced:g} {uom} en {len(invoices)} factura(s) "
            f"por {symbol} {amount_invoiced:.2f}."
        )
    else:
        message += f"No hay facturas de cliente publicadas con este producto {period}."

    return {
        "ok": True,
        "message": message,
        "data": {
            "product": label,
            "product_code": product.default_code or "",
            "qty_available": qty,
            "location": location_name,
            "date_from": date_from,
            "date_to": date_to,
            "qty_invoiced": qty_invoiced,
            "amount_invoiced": amount_invoiced,
            "invoice_count": len(invoices),
            "uom": uom,
        },
    }
