# -*- coding: utf-8 -*-
"""Textos de ayuda del Asistente ERP."""

from markupsafe import Markup

HELP_TITLE = "Consultas que puedo responder (solo lectura):"

HELP_SECTIONS = [
    (
        "Facturas",
        [
            "¿Está pagada la factura INV/2026/00003?",
            "¿Cuántos productos tiene la factura INV/2026/00003?",
        ],
    ),
    (
        "Inventario",
        [
            "¿Cuántas unidades hay del CAS-001?",
            "¿Hay stock del casco negro?",
        ],
    ),
    (
        "Ventas",
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
        [
            "¿Quién es el vendedor de Moto Racing Cuenca?",
        ],
    ),
    (
        "Stock y facturación",
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


def build_help_markup():
    """HTML para /help y mensajes de bienvenida."""
    parts = [
        Markup("<p><b>%s</b></p>") % HELP_TITLE,
    ]
    for title, examples in HELP_SECTIONS:
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
