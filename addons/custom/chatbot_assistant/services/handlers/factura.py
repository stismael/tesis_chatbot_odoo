# -*- coding: utf-8 -*-
"""CU-01: consultar factura (cabecera y/o líneas de producto)."""

import re

PAYMENT_LABELS = {
    "not_paid": "no pagada",
    "in_payment": "en proceso de pago",
    "paid": "pagada",
    "partial": "parcialmente pagada",
    "reversed": "revertida",
    "invoicing_legacy": "legado",
}

_PRODUCT_FOCUS_RE = re.compile(
    r"product|l[ií]nea|cu[aá]nt[oa]s?|detalle|art[ií]cul|item|cantidad",
    re.IGNORECASE,
)


def _invoice_product_lines(move):
    """Líneas de producto de la factura (excluye secciones/notas)."""
    lines = move.invoice_line_ids.filtered(
        lambda l: l.display_type in (False, "product") and (l.product_id or l.name)
    )
    rows = []
    for line in lines:
        name = line.product_id.display_name if line.product_id else (line.name or "Sin nombre")
        rows.append({
            "name": name,
            "quantity": line.quantity,
            "price_subtotal": line.price_subtotal,
        })
    return rows


def _focus_from_text(user_text):
    text = user_text or ""
    if _PRODUCT_FOCUS_RE.search(text):
        return "productos"
    return "resumen"


def handle(env, entities, user_text=""):
    Move = env["account.move"]
    invoice_number = entities.get("invoice_number")
    customer_name = entities.get("customer_name")
    focus = _focus_from_text(user_text)

    domain = [("move_type", "=", "out_invoice"), ("state", "=", "posted")]
    if invoice_number:
        domain.append(("name", "=", invoice_number))
    elif customer_name:
        partners = env["res.partner"].search([("name", "ilike", customer_name)], limit=5)
        if not partners:
            return {
                "ok": False,
                "message": f'No encontré un cliente con el nombre "{customer_name}".',
                "data": {},
            }
        if len(partners) > 1:
            names = ", ".join(partners.mapped("name"))
            return {
                "ok": False,
                "status": "ambiguous",
                "message": f"Hay varios clientes similares: {names}. Indique el nombre exacto.",
                "data": {"candidates": partners.mapped("name")},
            }
        domain.append(("partner_id", "=", partners.id))
    else:
        return {
            "ok": False,
            "message": "Indique el número de factura o el nombre del cliente.",
            "data": {},
        }

    moves = Move.search(domain, order="invoice_date desc, id desc", limit=10)
    if not moves:
        if invoice_number:
            return {
                "ok": False,
                "message": f"No encontré la factura {invoice_number}.",
                "data": {},
            }
        return {
            "ok": False,
            "message": f'No hay facturas publicadas para el cliente "{customer_name}".',
            "data": {},
        }

    lines = []
    data_rows = []
    for move in moves:
        pay = PAYMENT_LABELS.get(move.payment_state, move.payment_state or "desconocido")
        total = move.amount_total
        currency = move.currency_id.symbol or move.currency_id.name or "USD"
        partner = move.partner_id.name or ""
        product_rows = _invoice_product_lines(move)
        lines.append(
            f"- {move.name}: cliente {partner}, total {currency} {total:.2f}, "
            f"estado de pago: {pay}, productos: {len(product_rows)}."
        )
        data_rows.append({
            "name": move.name,
            "partner": partner,
            "amount_total": total,
            "payment_state": move.payment_state,
            "invoice_date": str(move.invoice_date or ""),
            "product_count": len(product_rows),
            "products": product_rows,
        })

    if invoice_number and len(moves) == 1:
        m = moves[0]
        pay = PAYMENT_LABELS.get(m.payment_state, m.payment_state or "desconocido")
        currency = m.currency_id.symbol or m.currency_id.name or "USD"
        product_rows = _invoice_product_lines(m)
        count = len(product_rows)

        if focus == "productos":
            if not product_rows:
                message = (
                    f"La factura {m.name} del cliente {m.partner_id.name} "
                    f"no tiene líneas de producto."
                )
            else:
                detail = "\n".join(
                    f"- {p['name']}: cantidad {p['quantity']:g}"
                    for p in product_rows
                )
                message = (
                    f"La factura {m.name} del cliente {m.partner_id.name} "
                    f"tiene {count} producto(s):\n{detail}"
                )
        else:
            message = (
                f"La factura {m.name} del cliente {m.partner_id.name} "
                f"tiene un total de {currency} {m.amount_total:.2f} y está {pay}."
            )
            if product_rows:
                message += f" Incluye {count} producto(s)."
    else:
        message = "Facturas encontradas:\n" + "\n".join(lines)

    return {"ok": True, "message": message, "data": {"invoices": data_rows, "focus": focus}}
