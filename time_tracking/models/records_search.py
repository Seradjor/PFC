from odoo import models, fields, api
from odoo.exceptions import UserError

class records_search(models.TransientModel):
    _name = 'time_tracking.records_search'
    _description = 'Búsqueda fichajes'

    date_start = fields.Date(string='Día inicial', required=True)
    date_end = fields.Date(string='Día final', required=True)

    # Relación con empleado
    employee_id = fields.Many2one('hr.employee', string='Empleado',required=True)

    def action_search_records(self):

        self.ensure_one()

        if self.date_start > fields.Date.today():
            raise UserError("Día inicial no puede ser posterior al día de hoy.")

        if self.date_end < self.date_start:
            raise UserError("Día final no puede ser anterior al día inicial.")
        
        domain = self._build_domain()

        records = self.env['time_tracking.record'].search(domain)

        if not records:
            raise UserError('Fichajes para el empleado y las fechas indicadas no encontrados.')

        return {
            'type': 'ir.actions.act_window',
            'name': 'Fichajes empleado',
            'res_model': 'time_tracking.record',
            'view_mode': 'tree',
            'views': [
                (self.env.ref('time_tracking.time_tracking_records_list').id, 'tree'),
                (False, 'form')
            ],
            'domain': domain,
            'context': {
                'employee_id': self.employee_id.id,
                'date_start': self.date_start,
                'date_end': self.date_end,
                'group_by': ['date:day']
            }
        }
    
    # Construye el dominio de búsqueda.
    def _build_domain(self):
        return [
            ('employee_id', '=', self.employee_id.id),
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
        ]




