from odoo import models, fields
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

        service = self.env['time_tracking.report_service']

        # Obtenemos fichajes.
        records = service._get_records(
            self.employee_id.id,
            self.date_start,
            self.date_end
        )

        if not records:
            raise UserError('Fichajes para el empleado y las fechas indicadas no encontrados.')

        lines, summary = service._generate_report(
            self.date_start,
            self.date_end,
            records
        )

        # Redirección al controller
        url = f"/time_tracking/report/{self.employee_id.id}/{self.date_start}/{self.date_end}"

        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'self',
        }
