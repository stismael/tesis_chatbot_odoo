# -*- coding: utf-8 -*-
"""
Resultados extensos: vista previa corta en el chat, enlace «Ver todo» a la lista de Odoo y
descarga en CSV con los campos autorizados de cada modelo.
"""
import csv
import io

# Filas que se muestran en el chat antes de ofrecer «Ver todo» y la descarga en CSV.
PREVIEW_ROWS = 5

# Columnas del CSV por modelo: (encabezado, ruta del campo). Solo campos autorizados (Tabla 6).
EXPORT_COLUMNS = {
    "account.move": [
        ("Factura", "name"),
        ("Cliente", "partner_id"),
        ("Fecha", "invoice_date"),
        ("Vencimiento", "invoice_date_due"),
        ("Total", "amount_total"),
        ("Saldo pendiente", "amount_residual"),
        ("Estado de pago", "payment_state"),
    ],
    "sale.order": [
        ("Pedido", "name"),
        ("Cliente", "partner_id"),
        ("Vendedor", "user_id"),
        ("Fecha", "date_order"),
        ("Total", "amount_total"),
        ("Estado", "state"),
    ],
    "sale.order.line": [
        ("Pedido", "order_id.name"),
        ("Cliente", "order_id.partner_id"),
        ("Fecha", "order_id.date_order"),
        ("Producto", "product_id"),
        ("Cantidad", "product_uom_qty"),
        ("Subtotal", "price_subtotal"),
        ("Estado", "order_id.state"),
    ],
}


def records_ref(records, title):
    """Referencia a todos los registros del resultado, para guardarla en la auditoría."""
    return {"model": records._name, "ids": records.ids, "title": title}


def preview_note(shown, total, noun):
    """Texto que indica que el chat muestra solo una parte del resultado."""
    if total <= shown:
        return ""
    return f"\nMostrando {shown} de {total} {noun}."


def _cell(record, path):
    """Valor legible de un campo (sigue relaciones con puntos; Many2one → nombre, selección → etiqueta)."""
    *parents, name = path.split(".")
    for parent in parents:
        record = record[parent]
    field = record._fields[name]
    value = record[name]
    if field.type == "many2one":
        return value.display_name or ""
    if field.type == "selection":
        return dict(field._description_selection(record.env)).get(value, value or "")
    if field.type in ("date", "datetime"):
        return field.to_string(value) if value else ""
    if field.type in ("float", "monetary"):
        return f"{value:.2f}"
    return "" if value is False else value


def build_csv(records):
    """CSV (UTF-8 con BOM, para que Excel muestre bien las tildes) de los registros dados."""
    columns = EXPORT_COLUMNS[records._name]
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([header for header, _path in columns])
    for record in records:
        writer.writerow([_cell(record, path) for _header, path in columns])
    return ("﻿" + buffer.getvalue()).encode("utf-8")
