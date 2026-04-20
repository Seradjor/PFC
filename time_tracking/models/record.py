from odoo import models, fields, api
from datetime import datetime


class record(models.Model):
    _name = 'time_tracking.record'
    _description = 'Time tracking records'
    _rec_name = 'record_id'

    record_id = fields.Integer(string='ID fichaje', readonly=True)
    barcode = fields.Char(string="Código empleado", store=False)
    date = fields.Date(string='Fecha', required=True)
    time = fields.Float(string='Hora', group_operator=False, required=True)
    type = fields.Selection([('entry', 'Entrada'),('exit', 'Salida')], string='Tipo', required=True)

    # Relación con empleado
    employee_id = fields.Many2one('hr.employee', string='Empleado',required=True)

    @api.model
    def create(self, vals):
        # Obtener el barcode
        barcode = vals.get('barcode')

        if barcode:
            # Buscar el empleado por barcode
            employee = self.env['hr.employee'].search([('barcode', '=', barcode)], limit=1)
            if not employee:
                raise ValueError(f"No existe ningún empleado con el código {barcode}")

            # Sustituir barcode por employee_id
            vals['employee_id'] = employee.id
            vals.pop('barcode', None)

        # Obtener el empleado
        employee_id = vals.get('employee_id')

        # Buscar el último registro de ese empleado
        last_record = self.search(
            [('employee_id', '=', employee_id)],
            order='record_id desc',
            limit=1
        )

        # Calcular el siguiente record_id
        if last_record:
            next_id = last_record.record_id + 1 
        else:
            next_id = 1

        vals['record_id'] = next_id

        # Autocompletar fecha/hora si no vienen informadas
        if not vals.get('date') or not vals.get('time'):
            now = datetime.now()
            vals['date'] = vals.get('date') or now.date()
            vals['time'] = vals.get('time') or now.hour + now.minute/60 + now.second/3600

        # Autodetectar tipo (Entry/Exit) si no viene informado
        if not vals.get('type'):
            last_today = self.search(
                [
                    ('employee_id', '=', employee_id),
                    ('date', '=', vals['date'])
                ],
                order='time desc',
                limit=1
            )

            if last_today and last_today.type == 'entry':
                vals['type'] = 'exit'
            else:
                vals['type'] = 'entry'

        # Evitar duplicados (employee_id + record_id)
        exists = self.search([
            ('employee_id', '=', employee_id),
            ('record_id', '=', next_id)
        ], limit=1)

        if exists:
            raise ValueError(f"El fichaje {next_id} ya existe para el empleado {employee_id}")

        return super().create(vals)
    

    """ BUTTONS FUNCTIONS """

    def action_open_edit_day(self):
    # Abrir vista de edición de fichajes del día
        return {
            'type': 'ir.actions.act_window',
            'name': 'Editar fichajes del día',
            'res_model': 'time_tracking.record',
            'view_mode': 'tree,form',
            'domain': [
                ('employee_id', '=', self.employee_id.id),
                ('date', '=', self.date)
            ],
            'context': {
                'default_employee_id': self.employee_id.id,
                'default_date': self.date,
            }
        }       

    def action_save_day(self):
        return {
            'type': 'ir.actions.act_window_close'
        }        

