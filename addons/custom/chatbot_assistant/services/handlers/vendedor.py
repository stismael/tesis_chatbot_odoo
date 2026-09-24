# -*- coding: utf-8 -*-
"""CU-04: consultar vendedor asignado al cliente."""


def handle(env, entities, user_text=""):
    customer_name = entities.get("customer_name")
    if not customer_name:
        return {
            "ok": False,
            "message": "Indique el nombre del cliente.",
            "data": {},
        }

    partners = env["res.partner"].search([
        ("name", "ilike", customer_name),
        ("customer_rank", ">", 0),
    ], limit=5)
    if not partners:
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

    partner = partners[0]
    salesperson = partner.user_id
    if not salesperson:
        return {
            "ok": False,
            "message": f'El cliente "{partner.name}" no tiene vendedor asignado.',
            "data": {"partner": partner.name, "salesperson": None},
        }

    sp_partner = salesperson.partner_id
    phone = sp_partner.phone or sp_partner.mobile or "no registrado"
    email = salesperson.login or sp_partner.email or "no registrado"
    message = (
        f'El vendedor asignado a "{partner.name}" es {salesperson.name}. '
        f"Correo: {email}. Teléfono: {phone}."
    )
    return {
        "ok": True,
        "message": message,
        "data": {
            "partner": partner.name,
            "salesperson": salesperson.name,
            "email": email,
            "phone": phone,
        },
    }
