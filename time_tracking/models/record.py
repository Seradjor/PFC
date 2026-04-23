from odoo import models, fields, api
from odoo.exceptions import UserError
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
    duration = fields.Float(string='Duración', store=True)

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

        # Buscar el último registro de ese empleado y calculamos nuevo id
        vals['record_id'] = self._get_next_record_id(employee_id)

        # Autocompletar fecha/hora si no vienen informadas
        if not vals.get('date') or not vals.get('time'):
            now = datetime.now()
            vals['date'] = vals.get('date') or now.date()
            vals['time'] = vals.get('time') or (now.hour + 2) + now.minute/60 + now.second/3600

        # Autodetectar tipo (Entry/Exit) si no viene informado
        if not vals.get('type'):
            vals['type'] = self._calculate_type(employee_id, vals['date'], vals['time'])

        # Calculamos la duración del tiempo trabajado, en caso de ser una salida.
        vals['duration'] = self._calculate_duration(employee_id, vals['date'], vals['time'], vals['type'])

        # Evitar duplicados (employee_id + record_id)
        exists = self.search([
            ('employee_id', '=', employee_id),
            ('record_id', '=', vals['record_id'])
        ], limit=1)

        if exists:
            raise ValueError(f"El fichaje {vals['record_id']} ya existe para el empleado {employee_id}")

        record = super().create(vals)

        # Recalcular día completo
        record._recompute_day(record.employee_id.id, record.date)

        return record
    

    def write(self, vals):

        # Si viene de _recompute_day, no recalcular otra vez
        if self.env.context.get('skip_recompute'):
            return super().write(vals)

        result = super().write(vals)

        # Recalcular día completo
        for record in self:
            record._recompute_day(record.employee_id.id, record.date)

        # Añadimos un flag al contexto para que el JS refresque la vista
        self.env.context = dict(self.env.context, force_reload=True)

        return result  


    
    def _calculate_type(self, employee_id, date, time):

        previous_record = self._get_previous_record(employee_id, date, time)

        if previous_record and previous_record.type == 'entry':
            return 'exit'
        else:
            return 'entry'
        

        
    def _calculate_duration(self, employee_id, date, time, type):

        # Buscar el registro anterior en el tiempo
        previous_record = self._get_previous_record(employee_id, date, time)

        if previous_record and previous_record.type == 'entry' and type == 'exit':
            return max(0.0, time - previous_record.time)
        else:
            return 0.0
        

    def _recompute_day(self, employee_id, date):

        day_records = self._get_day_records(employee_id, date)

        for record in day_records:
            duration = self._calculate_duration(record.employee_id.id, record.date, record.time, record.type)
            record.with_context(skip_recompute=True).write({'duration': duration})
        


    def _get_employee_from_barcode(self, barcode):
        employee = self.env['hr.employee'].search([('barcode', '=', barcode)], limit=1)
        return employee
    

    def _get_day_records(self, employee_id, date):
        day_records = self.search(
            [
                ('employee_id', '=', employee_id),
                ('date', '=', date)
            ],
            order='time asc'
        )

        return day_records
    
    

    def _get_previous_record(self, employee_id, date, time):
        # Buscar el registro anterior en el tiempo
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
    

    def _get_next_record_id(self, employee_id):
        last_record = self.search(
            [('employee_id', '=', employee_id)],
            order='record_id desc',
            limit=1
        )
        return (last_record.record_id + 1) if last_record else 1
    
    

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

            # Creamos fichaje, recalculando el resto de campos.
            new_record = self.create({
                'employee_id': employee.id,
            })

            # Respuesta para el popup
            return {
                'status': 'ok',
                'title': 'Fichaje registrado',
                'message': f"{employee.name} - { 'Entrada' if new_record.type=='entry' else 'Salida' } registrada correctamente."
            }

        except Exception as e:
            # Log interno para depuración
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
        date_start = datetime.strptime(date_start, "%Y-%m-%d").date()
        date_end = datetime.strptime(date_end, "%Y-%m-%d").date()

        return employee_id, date_start, date_end
    
    # NECESARIO??
    def _get_records_for_report(self):
        employee_id, date_start, date_end = self._get_context()

        records = self.search([
            ('employee_id', '=', employee_id),
            ('date', '>=', date_start),
            ('date', '<=', date_end),
        ])

        return records, employee_id, date_start, date_end


    def _get_service(self):
        return self.env['time_tracking.report_service']


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

    def action_export_pdf(self):
        records, employee_id, date_start, date_end = self._get_records_for_report()

        employee = self.env['hr.employee'].browse(employee_id)
        service = self._get_service()

        lines, summary = service._generate_report(date_start, date_end, records)

        data = {
            'employee_name': employee.name,
            'date_start': date_start.strftime("%d/%m/%Y"),
            'date_end': date_end.strftime("%d/%m/%Y"),
            'lines': lines,
            'total_worked_hours': summary['total_worked_hours'],
            'expected_hours': summary['expected_hours'],
            'hours_difference': summary['hours_difference'],
            'extra_hours': summary['extra_hours'],
            'holiday_hours': summary['holiday_hours'],
            'extra_holiday_value': summary['extra_holiday_value'],
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
            'target': 'self',
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
                'type': 'success',
        }
    }

    

    
    
    

