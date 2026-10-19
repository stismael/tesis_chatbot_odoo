# -*- coding: utf-8 -*-
"""Textos de ayuda del Asistente ERP."""

from markupsafe import Markup

HELP_TITLE = "Consultas que puedo responder (solo lectura):"

HELP_SECTIONS = [
    (
        "Facturas",
        "consultar_factura",
        [
            "¿Está pagada la factura INV/2026/00003?",
            "¿Cuántos productos tiene la factura INV/2026/00003?",
        ],
    ),
    (
        "Inventario",
        "consultar_stock",
        [
            "¿Cuántas unidades hay del CAS-001?",
            "¿Hay stock del casco negro?",
        ],
    ),
    (
        "Ventas",
        "consultar_ventas_cliente",
        [
            "¿Cuántas ventas hay del CAS-001?",
            "¿Qué ventas tiene Comercial Andina S.A.?",
            "¿Cuál fue la venta con mayor cantidad de este producto?",
            "¿Qué cliente ha comprado más este producto?",
            "Lista los pedidos del CAS-001",
        ],
    ),
    (
        "Vendedor",
        "consultar_vendedor_cliente",
        [
            "¿Quién es el vendedor de Moto Racing Cuenca?",
        ],
    ),
    (
        "Stock y facturación",
        "consultar_stock_facturacion_producto",
        [
            "¿Cuánto stock queda del FIL-M01 y cuánto se facturó este mes?",
            "Stock y facturación de la bujía NGK durante julio",
        ],
    ),
]

HELP_FOOTER = (
    "Escribe tu pregunta en lenguaje natural. "
    "En este chat recuerdo el producto o cliente de los últimos mensajes."
)


NO_ACCESS_TEXT = (
    "Con tus permisos actuales no puedes hacer consultas al asistente. "
    "Pide acceso al administrador."
)


def build_help_markup(allowed_intents=None):
    """HTML para /help. Si se indica `allowed_intents`, solo muestra esas consultas."""
    sections = [
        section for section in HELP_SECTIONS
        if allowed_intents is None or section[1] in allowed_intents
    ]
    parts = [
        Markup("<p><b>%s</b></p>") % HELP_TITLE,
    ]
    if not sections:
        parts.append(Markup("<p>%s</p>") % NO_ACCESS_TEXT)
    for title, _intent, examples in sections:
        parts.append(Markup("<p><b>%s</b></p><ul>") % title)
        for example in examples:
            parts.append(Markup("<li><i>%s</i></li>") % example)
        parts.append(Markup("</ul>"))
    parts.append(Markup("<p>%s</p>") % HELP_FOOTER)
    parts.append(Markup("<p><i>Escribe %s para ver esta ayuda cuando quieras.</i></p>") % Markup("<b>/help</b>"))
    return Markup("").join(parts)


def build_welcome_markup():
    return Markup(
        "<p>Hola, soy el <b>Asistente ERP</b>.</p>"
        "<p>Puedo consultar facturas, inventario, ventas, vendedores y facturación por producto.</p>"
        "<p>Escribe tu pregunta o <b>/help</b> para ver ejemplos.</p>"
    )
