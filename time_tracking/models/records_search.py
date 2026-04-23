from odoo import models, fields, api
from odoo.exceptions import UserError
from ..utils import constants
from datetime import timedelta

class records_search(models.TransientModel):
    _name = 'time_tracking.records_search'
    _description = 'Búsqueda fichajes'

    date_start = fields.Date(string='Día inicial', required=True)
    date_end = fields.Date(string='Día final', required=True)

    # Relación con empleado
    employee_id = fields.Many2one('hr.employee', string='Empleado',required=True)

    def action_search_records(self):

        self.ensure_one()

        records = self.env['time_tracking.record'].search([
            ('employee_id', '=', self.employee_id.id),
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
        ])

        if not records:
            raise UserError('Fichajes para el empleado y las fechas indicadas no encontrados.')

        return {
            'type': 'ir.actions.act_window',
            'name': 'Fichajes empleado',
            'res_model': 'time_tracking.record',
            'view_mode': 'tree',
            'views': [
                (self.env.ref('time_tracking.time_tracking_records_list').id, 'tree'),
                (False, 'form'),
            ],
            'domain': [
                ('employee_id', '=', self.employee_id.id),
                ('date', '>=', self.date_start),
                ('date', '<=', self.date_end),
            ],
            'context': {
                'employee_id': self.employee_id.id,
                'date_start': self.date_start,
                'date_end': self.date_end,
                'group_by': ['date:day'],
            },
        }




