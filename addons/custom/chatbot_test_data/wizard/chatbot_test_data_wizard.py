# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ChatbotTestDataWizard(models.TransientModel):
    _name = 'chatbot.test.data.wizard'
    _description = 'Asistente para generar datos sintéticos de chatbot'

    confirm = fields.Boolean(
        string='Confirmar generación',
        help='Los datos se generan una sola vez por base de datos.',
    )

    def action_generate(self):
        self.ensure_one()
        if not self.confirm:
            raise UserError(_('Marque la casilla de confirmación para continuar.'))
        self.env['chatbot.test.data.generator'].generate_all()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Datos generados'),
                'message': _('Datos de demostración creados correctamente.'),
                'type': 'success',
                'sticky': False,
            },
        }
