from odoo import models, fields


class records_search(models.TransientModel):
    _name = 'time_tracking.records_search'
    _description = 'Búsqueda fichajes'

    date_start = fields.Date(string='Día inicial', required=True)
    date_end = fields.Date(string='Día final', required=True)

    # Relación con empleado
    employee_id = fields.Many2one('hr.employee', string='Empleado',required=True)

    def action_search_records(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Fichajes del empleado',
            'res_model': 'time_tracking.record',
            'view_mode': 'tree,form',
            'domain': [
                ('employee_id', '=', self.employee_id.id),
                ('date', '>=', self.date_start),
                ('date', '<=', self.date_end),
            ],
        }
