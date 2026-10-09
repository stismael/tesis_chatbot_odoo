# -*- coding: utf-8 -*-
"""CU-02: consultar stock / inventario."""


def available_qty(env, product, location_name=None):
    """Cantidad disponible del producto; None si la ubicación indicada no existe."""
    if not location_name:
        return product.qty_available
    locations = env["stock.location"].search([
        ("usage", "=", "internal"),
        ("complete_name", "ilike", location_name),
    ], limit=5)
    if not locations:
        return None
    quants = env["stock.quant"].search([
        ("product_id", "=", product.id),
        ("location_id", "in", locations.ids),
    ])
    return sum(quants.mapped(lambda q: q.quantity - q.reserved_quantity))


def handle(env, entities, user_text=""):
    product_code = entities.get("product_code")
    product_name = entities.get("product_name")
    location_name = entities.get("location_name")

    Product = env["product.product"]
    domain = [("active", "=", True)]
    if product_code:
        domain.append(("default_code", "=ilike", product_code))
    elif product_name:
        domain.append(("name", "ilike", product_name))
    else:
        return {
            "ok": False,
            "message": "Indique el código o el nombre del producto.",
            "data": {},
        }

    products = Product.search(domain, limit=5)
    if not products:
        label = product_code or product_name
        return {
            "ok": False,
            "message": f'No encontré el producto "{label}".',
            "data": {},
        }
    if len(products) > 1 and product_name and not product_code:
        names = ", ".join(
            f"{p.display_name} ({p.default_code or 'sin código'})" for p in products
        )
        return {
            "ok": False,
            "status": "ambiguous",
            "message": f"Hay varios productos similares: {names}. Precise el código o el nombre.",
            "data": {"candidates": products.mapped("display_name")},
        }

    product = products[0]
    qty = available_qty(env, product, location_name)
    if qty is None:
        return {
            "ok": False,
            "message": f'No encontré la ubicación "{location_name}".',
            "data": {},
        }

    code = product.default_code or "sin código"
    uom = product.uom_id.name or "Ud"
    loc_msg = f' en ubicación "{location_name}"' if location_name else " (ubicaciones internas)"
    message = (
        f"El producto {product.display_name} ({code}) tiene "
        f"{qty:.0f} {uom} disponibles{loc_msg}."
    )
    return {
        "ok": True,
        "message": message,
        "data": {
            "product_id": product.id,
            "product_name": product.display_name,
            "product_code": code,
            "qty_available": qty,
            "uom": uom,
        },
    }
