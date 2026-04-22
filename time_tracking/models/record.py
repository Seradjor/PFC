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
    
    @api.model
    def nfc_register(self, barcode):

        try:
            import logging
            _logger = logging.getLogger(__name__)


            # Buscamos empleado por barcode
            employee = self.env['hr.employee'].search([('barcode', '=', barcode)], limit=1)

            if not employee:
                return {
                    'status': 'error',
                    'title': 'Tarjeta no registrada',
                    'message': 'No existe ningún empleado con esta tarjeta.'
                }

            # Obtenemos la fecha y hora actual (sumándole 2 horas para ajustar a hora real) para realizar el fichaje
            now = fields.Datetime.now()
            today = now.date()
            hour_float = (now.hour + 2) + now.minute / 60.0

            # Determinar si es entrada o salida
            last_record = self.search([
                ('employee_id', '=', employee.id),
                ('date', '=', today)
            ], order="time desc", limit=1)

            if not last_record:
                record_type = 'entry'
            else:
                record_type = 'exit' if last_record.type == 'entry' else 'entry'

            # Creamos registro
            self.create({
                'employee_id': employee.id,
                'date': today,
                'time': hour_float,
                'type': record_type,
            })

            # Respuesta para el popup
            return {
                'status': 'ok',
                'title': 'Fichaje registrado',
                'message': f"{employee.name} - { 'Entrada' if record_type=='entry' else 'Salida' } registrada correctamente."
            }

        except Exception as e:
            # Log interno para depuración
            _logger.error("Error en nfc_register: %s", e)

            return {
                'status': 'error',
                'title': 'Error inesperado',
                'message': 'Ha ocurrido un error al registrar el fichaje.'
            }
    

    def _get_employee_from_barcode(self, barcode):
        employee = self.env['hr.employee'].search([('barcode', '=', barcode)], limit=1)
        return employee
    

    def _get_next_record_id(self, employee_id):
        last = self.search(
            [('employee_id', '=', employee_id)],
            order='record_id desc',
            limit=1
        )
        return (last.record_id + 1) if last else 1
    

    def _get_current_datetime(self):
        now = datetime.now()
        return now.date(), (now.hour + 2) + now.minute / 60 + now.second / 3600 # Sumamos 2 horas para ajustar a hora real.
    

    def _get_record_type(self, employee_id, date):

        last_today = self.search(
            [
                ('employee_id', '=', employee_id),
                ('date', '=', date)
            ],
            order='time desc',
            limit=1
        )

        if last_today and last_today.type == 'entry':
            return 'exit'
        else:
            return 'entry'


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


    def action_generate_report_from_list(self):
        context = self.env.context

        employee_id = context.get('employee_id')
        date_start = context.get('date_start')
        date_end = context.get('date_end')

        records_search = self.env['time_tracking.records_search'].create({
            'employee_id': employee_id,
            'date_start': date_start,
            'date_end': date_end,
        })

        return records_search.action_search_records_report()
    

    def action_export_pdf(self):
        pass

    def action_export_csv(self):
        pass

