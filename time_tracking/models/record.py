from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
from ..utils import constants
import logging

_logger = logging.getLogger(__name__)

class record(models.Model):
    _name = 'time_tracking.record'
    _description = 'Time tracking records'
    _rec_name = 'record_id'

    record_id = fields.Integer(string='ID fichaje', readonly=True)
    date = fields.Date(string='Fecha', required=True, default=fields.Date.context_today)
    time = fields.Float(string='Hora', group_operator=False, required=True, default=lambda self: self._default_time())
    type = fields.Selection([('entry', 'Entrada'),('exit', 'Salida')], string='Tipo', required=True)
    duration = fields.Float(string='Duración', compute="_compute_duration", store=True)

    # Relación con empleado.
    employee_id = fields.Many2one('hr.employee', string='Empleado',required=True)

    @api.model
    def create(self, vals):
        # Obtener el empleado.
        employee_id = vals.get('employee_id')

        # Buscar el último registro de ese empleado y calculamos nuevo id.
        vals['record_id'] = self._get_next_record_id(employee_id)

        # Autocompletar fecha/hora si no vienen informadas.
        if not vals.get('date') or not vals.get('time'):
            vals['date'] = vals.get('date') or fields.Date.context_today(self)
            vals['time'] = vals.get('time') or self._default_time()

        # Autodetectar tipo (Entry/Exit) si no viene informado.
        if not vals.get('type'):
            vals['type'] = self._calculate_type(employee_id, vals['date'], vals['time'])
        
        return super().create(vals)
    

    def _get_next_record_id(self, employee_id):
        next_record_id = 1

        last_record = self.search(
            [('employee_id', '=', employee_id)],
            order='record_id desc',
            limit=1
        )

        if last_record:
            next_record_id = (last_record.record_id + 1)

        return next_record_id
    
    
    def _default_time(self):
        now = datetime.now()
        time = (now.hour + 2) + now.minute/60 + now.second/3600

        return time
    

    def _calculate_type(self, employee_id, date, time):

        previous_record = self._get_previous_record(employee_id, date, time)

        if previous_record and previous_record.type == 'entry':
            return 'exit'
        else:
            return 'entry'
        
    
    def _get_previous_record(self, employee_id, date, time):

        previous_record = self.search(
            [
                ('employee_id', '=', employee_id),
                ('date', '=', date),
                ('time', '<', time)
            ],
            order='time desc',
            limit=1
        )

        return previous_record
        

    @api.depends('employee_id', 'date', 'time', 'type')
    def _compute_duration(self):

        for record in self:
            day_records = self._get_day_records(record.employee_id.id, record.date)

            previous_record = None

            for day_record in day_records:
                if previous_record and previous_record.type == 'entry' and day_record.type == 'exit':
                    day_record.duration = max(0.0, day_record.time - previous_record.time)
                else:
                    day_record.duration = 0.0
                previous_record = day_record


    def _get_day_records(self, employee_id, date):
        day_records = self.search(
            [
                ('employee_id', '=', employee_id),
                ('date', '=', date)
            ],
            order='time asc'
        )

        return day_records
      

    @api.model
    def nfc_register(self, id_time_tracking):

        try:

            # Buscamos empleado por id_time_tracking.
            employee = self.env['hr.employee'].search([('id_time_tracking', '=', id_time_tracking)], limit=1)

            if not employee:
                return {
                    'status': 'error',
                    'title': 'Tarjeta no registrada',
                    'message': f"No existe ningún empleado con el ID {id_time_tracking}."
                }

            # Creamos fichaje, recalculando el resto de campos.
            new_record = self.create({'employee_id': employee.id})

            # Respuesta para el popup
            return {
                'status': 'ok',
                'title': 'Fichaje registrado',
                'message': f"{employee.name} - { 'Entrada' if new_record.type=='entry' else 'Salida' } registrada correctamente."
            }

        except Exception as e:
            # Log interno para depuración.
            _logger.error("Error en nfc_register: %s", e)

            return {
                'status': 'error',
                'title': 'Error inesperado',
                'message': 'Ha ocurrido un error al registrar el fichaje.'
            }
    
    # Obtenemos datos de la consulta de fichajes para las acciones posteriores de los botones de la consulta.
    def _get_context(self):
        context = self.env.context

        employee_id = context.get('employee_id')
        date_start = context.get('date_start')
        date_end = context.get('date_end')

        if not all([employee_id, date_start, date_end]):
            raise UserError("Faltan datos para generar el informe.")

        employee_id = int(employee_id)
        date_start = datetime.strptime(date_start, constants.FORMATO_FECHA_DATE).date()
        date_end = datetime.strptime(date_end, constants.FORMATO_FECHA_DATE).date()

        return employee_id, date_start, date_end
    
    def _get_records_for_report(self):
        employee_id, date_start, date_end = self._get_context()

        records = self.search([
            ('employee_id', '=', employee_id),
            ('date', '>=', date_start),
            ('date', '<=', date_end)
        ])

        return records, employee_id, date_start, date_end


    def _get_service(self):
        return self.env['time_tracking.report_service']


    """ Buttons functions """      

    def action_save_day(self):
        self.ensure_one()

        if self.date > fields.Date.today():
            raise UserError("La fecha no puede ser posterior a hoy.")

        if (self.time < constants.HORA_MIN or self.time > constants.HORA_MAX):
            raise UserError(
                f"La hora debe estar entre las {constants.HORA_MIN:02.0f}:00 y las {constants.HORA_MAX:02.0f}:00."
            )

        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }
    

    def action_export_pdf(self):
        records, employee_id, date_start, date_end = self._get_records_for_report()

        employee = self.env['hr.employee'].browse(employee_id)
        service = self._get_service()
        lines, summary = service._generate_report(date_start, date_end, records)

        data = {
            'employee_name': employee.name,
            'date_start': date_start.strftime(constants.FORMATO_FECHA_INFORME),
            'date_end': date_end.strftime(constants.FORMATO_FECHA_INFORME),
            'lines': lines,
            'total_worked_hours': summary['total_worked_hours'],
            'expected_hours': summary['expected_hours'],
            'hours_difference': summary['hours_difference'],
            'extra_hours': summary['extra_hours'],
            'holiday_hours': summary['holiday_hours'],
            'extra_holiday_value': summary['extra_holiday_value']
        }

        return self.env.ref('time_tracking.action_report_time_tracking').report_action(
            records,
            data=data
        )
    

    def action_export_csv(self):
        
        employee_id, date_start, date_end = self._get_context()

        return {
            'type': 'ir.actions.act_url',
            'url': f'/time_tracking/report/csv/{employee_id}/{date_start}/{date_end}',
            'target': 'self'
        }


    def action_send_email(self):
        employee_id, date_start, date_end = self._get_context()

        employee = self.env['hr.employee'].browse(employee_id)

        service = self._get_service()

        service.send_employee_report(employee, date_start, date_end)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Email enviado',
                'message': f'Informe enviado a {employee.private_email}',
                'type': 'success'
        }
    }

    

    
    
    

