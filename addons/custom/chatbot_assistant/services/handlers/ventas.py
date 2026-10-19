# -*- coding: utf-8 -*-
"""CU-03: consultar ventas por cliente y/o producto."""

import re

from .access import scope_note

STATE_LABELS = {
    "draft": "borrador",
    "sent": "enviado",
    "sale": "pedido de venta",
    "done": "bloqueado",
    "cancel": "cancelado",
}

# Estado del pedido pedido en la consulta (entidad order_state); sin estado = pedidos confirmados.
ORDER_STATE_FILTERS = {
    "pedido": {
        "states": ["sale", "done"], "plural": "pedidos confirmados", "count": "pedido(s) confirmado(s)",
        "verb": "vendidas",
    },
    "cotizacion": {
        "states": ["draft", "sent"], "plural": "cotizaciones", "count": "cotización(es)",
        "verb": "cotizadas",
    },
    "cancelado": {
        "states": ["cancel"], "plural": "pedidos cancelados", "count": "pedido(s) cancelado(s)",
        "verb": "en pedidos cancelados",
    },
}


def _state_filter(entities):
    return ORDER_STATE_FILTERS.get(entities.get("order_state") or "pedido", ORDER_STATE_FILTERS["pedido"])


_LIST_RE = re.compile(
    r"list|lista|mu[eé]str|detall|pedidos|cotiz|ordenes|órdenes|enumera",
    re.IGNORECASE,
)
_MAX_QTY_RE = re.compile(
    r"mayor\s+cantidad|m[aá]s\s+cantidad|venta\s+m[aá]s\s+grande|"
    r"pedido\s+m[aá]s\s+grande|m[aá]s\s+unidades|m[aá]xim",
    re.IGNORECASE,
)
_TOP_CUSTOMER_RE = re.compile(
    r"cliente\s+.*(m[aá]s|mayor)|qui[eé]n\s+.*(m[aá]s|mayor)|compr[oó]\s+m[aá]s",
    re.IGNORECASE,
)


def _find_customer(env, customer_name):
    partners = env["res.partner"].search([
        ("name", "ilike", customer_name),
        ("customer_rank", ">", 0),
    ], limit=5)
    if not partners:
        partners = env["res.partner"].search([("name", "ilike", customer_name)], limit=5)
    return partners


def _find_product(env, product_code=None, product_name=None):
    Product = env["product.product"]
    if product_code:
        products = Product.search([("default_code", "=ilike", product_code)], limit=5)
        if products:
            return products
    if product_name:
        products = Product.search([("name", "ilike", product_name)], limit=5)
        if products:
            return products
    if product_code:
        products = Product.search([
            "|", ("default_code", "ilike", product_code), ("name", "ilike", product_code),
        ], limit=5)
        return products
    return Product.browse()


def _order_domain(entities, partner=None):
    domain = [("state", "in", _state_filter(entities)["states"])]
    if partner:
        domain.append(("partner_id", "=", partner.id))
    if entities.get("date_from"):
        domain.append(("date_order", ">=", entities["date_from"]))
    if entities.get("date_to"):
        domain.append(("date_order", "<=", entities["date_to"]))
    return domain


def _product_label(product):
    code = product.default_code
    name = product.name or product.display_name
    return f"{code} ({name})" if code else name


def _query_mode(user_text):
    text = user_text or ""
    if _LIST_RE.search(text):
        return "list"
    if _MAX_QTY_RE.search(text):
        return "max_quantity"
    if _TOP_CUSTOMER_RE.search(text):
        return "top_customer"
    return "summary"


def _get_product_lines(env, product, entities, partner=None):
    line_domain = [
        ("product_id", "=", product.id),
        ("order_id.state", "in", _state_filter(entities)["states"]),
    ]
    if partner:
        line_domain.append(("order_id.partner_id", "=", partner.id))
    if entities.get("date_from"):
        line_domain.append(("order_id.date_order", ">=", entities["date_from"]))
    if entities.get("date_to"):
        line_domain.append(("order_id.date_order", "<=", entities["date_to"]))
    return env["sale.order.line"].search(line_domain, order="id desc")


def _line_rows(lines_rec, currency):
    rows = []
    for line in lines_rec:
        order = line.order_id
        rows.append({
            "order": order.name,
            "partner": order.partner_id.name,
            "quantity": line.product_uom_qty,
            "price_subtotal": line.price_subtotal,
            "currency": currency,
        })
    return rows


def _format_list(rows, product_label, state):
    if not rows:
        return f"No hay {state['plural']} con {product_label}."
    lines = [
        f"- {r['order']}: {r['quantity']:g} uds, {r['currency']} {r['price_subtotal']:.2f} — {r['partner']}"
        for r in rows
    ]
    return f"Pedidos con {product_label} ({len(rows)}):\n" + "\n".join(lines)


def _sales_by_customer(env, partner, entities, user_text=""):
    state = _state_filter(entities)
    domain = _order_domain(entities, partner=partner)
    all_orders = env["sale.order"].search(domain, order="date_order desc")
    orders = all_orders[:15]
    if not orders:
        return {
            "ok": False,
            "message": f'No hay {state["plural"]} que puedas consultar para el cliente "{partner.name}".',
            "data": {"partner": partner.name},
        }

    total = sum(all_orders.mapped("amount_total"))
    currency = orders[0].currency_id.symbol or orders[0].currency_id.name or "USD"
    mode = _query_mode(user_text)

    if mode == "list":
        detail = [
            f"- {o.name}: {currency} {o.amount_total:.2f}"
            for o in orders
        ]
        count = f"{len(all_orders)}"
        if len(all_orders) > len(orders):
            count += f"; se muestran los {len(orders)} más recientes"
        message = f'{state["plural"].capitalize()} de "{partner.name}" ({count}):\n' + "\n".join(detail)
    else:
        message = (
            f'"{partner.name}" tiene {len(all_orders)} {state["count"]} '
            f"por un total de {currency} {total:.2f}. "
            f"Si quieres verlos, pídeme que los liste."
        )

    message += scope_note(env, "sale.order")
    return {
        "ok": True,
        "message": message,
        "data": {
            "partner": partner.name,
            "order_count": len(all_orders),
            "amount_total": total,
        },
    }


def _sales_by_product(env, product, entities, partner=None, user_text=""):
    state = _state_filter(entities)
    lines_rec = _get_product_lines(env, product, entities, partner=partner)
    label = _product_label(product)
    scope = f' para "{partner.name}"' if partner else ""

    if not lines_rec:
        return {
            "ok": False,
            "message": f"No hay {state['plural']} de {label}{scope} entre los que puedes consultar.",
            "data": {
                "product": label,
                "product_code": product.default_code or "",
                "partner": partner.name if partner else None,
            },
        }

    qty = sum(lines_rec.mapped("product_uom_qty"))
    amount = sum(lines_rec.mapped("price_subtotal"))
    orders = lines_rec.mapped("order_id")
    currency = (orders[:1].currency_id.symbol if orders else None) or "USD"
    rows = _line_rows(lines_rec, currency)
    mode = _query_mode(user_text)

    if mode == "max_quantity":
        best = max(rows, key=lambda r: r["quantity"])
        message = (
            f"La venta con mayor cantidad de {label} es {best['order']}: "
            f"{best['quantity']:g} unidades ({best['partner']}, "
            f"{best['currency']} {best['price_subtotal']:.2f})."
        )
    elif mode == "top_customer":
        totals = {}
        for row in rows:
            key = row["partner"]
            if key not in totals:
                totals[key] = {"qty": 0.0, "amount": 0.0, "orders": set()}
            totals[key]["qty"] += row["quantity"]
            totals[key]["amount"] += row["price_subtotal"]
            totals[key]["orders"].add(row["order"])
        top_name, top = max(totals.items(), key=lambda item: item[1]["qty"])
        message = (
            f"El cliente que más compró {label} es {top_name}: "
            f"{top['qty']:g} unidades en {len(top['orders'])} pedido(s) "
            f"({currency} {top['amount']:.2f})."
        )
    elif mode == "list":
        message = _format_list(rows, label, state)
    else:
        message = (
            f"{label}: {qty:g} unidades {state['verb']} en {len(orders)} {state['count']} "
            f"({currency} {amount:.2f}). "
            f"Si quieres el detalle por pedido, pídemelo."
        )

    message += scope_note(env, "sale.order")
    return {
        "ok": True,
        "message": message,
        "data": {
            "product": label,
            "product_code": product.default_code or "",
            "partner": partner.name if partner else None,
            "quantity": qty,
            "amount_subtotal": amount,
            "order_count": len(orders),
            "query_mode": mode,
        },
    }


def handle(env, entities, user_text=""):
    customer_name = entities.get("customer_name")
    product_code = entities.get("product_code")
    product_name = entities.get("product_name")

    partner = None
    if customer_name:
        partners = _find_customer(env, customer_name)
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
        partner = partners[0]

    if product_code or product_name:
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
        return _sales_by_product(
            env, products[0], entities, partner=partner, user_text=user_text,
        )

    if partner:
        return _sales_by_customer(env, partner, entities, user_text=user_text)

    return {
        "ok": False,
        "message": "Indique el nombre del cliente o el producto (código o nombre).",
        "data": {},
    }
