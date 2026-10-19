# -*- coding: utf-8 -*-
from odoo import api, fields, models

INTENTS = [
    ("consultar_factura", "Consultar factura (CU-01)"),
    ("consultar_stock", "Consultar stock (CU-02)"),
    ("consultar_ventas_cliente", "Consultar ventas (CU-03)"),
    ("consultar_vendedor_cliente", "Consultar vendedor asignado (CU-04)"),
    ("consultar_stock_facturacion_producto", "Stock y facturación por producto (CU-05)"),
]


class ChatbotIntentPermission(models.Model):
    """
    Permisos por consulta: grupos de Odoo que el asistente exige, además de los permisos
    propios de Odoo, para responder cada tipo de consulta. Solo afecta al chatbot.
    """

    _name = "chatbot.intent.permission"
    _description = "Permisos por consulta del chatbot"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    intent = fields.Selection(INTENTS, string="Consulta", required=True)
    area_label = fields.Char(
        string="Se informa como",
        required=True,
        help='Texto del mensaje al usuario sin permiso: "No tienes permiso para consultar <texto>."',
    )
    group_ids = fields.Many2many(
        "res.groups",
        "chatbot_intent_permission_group_rel",
        "permission_id",
        "group_id",
        string="Grupos exigidos",
        help="El usuario debe pertenecer a TODOS estos grupos (los administradores de cada módulo "
             "incluyen al usuario). Sin grupos, la consulta solo depende de los permisos de Odoo.",
    )
    note = fields.Text(string="Notas")

    _sql_constraints = [
        ("intent_uniq", "unique(intent)", "Ya existe una fila de permisos para esa consulta."),
    ]

    @api.model
    def _missing_groups(self, intent, user=None):
        """Grupos exigidos para `intent` que el usuario no tiene, y la fila aplicada."""
        user = user or self.env.user
        rule = self.sudo().search([("intent", "=", intent)], limit=1)
        if not rule:
            return self.env["res.groups"], rule
        return rule.group_ids.filtered(lambda g: g not in user.groups_id), rule

    @api.model
    def _allowed_intents(self, user=None):
        """Consultas que el usuario puede hacer según la tabla."""
        return [intent for intent, _label in INTENTS if not self._missing_groups(intent, user)[0]]
