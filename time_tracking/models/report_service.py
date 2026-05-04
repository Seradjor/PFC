from email.utils import formataddr

from odoo import models, fields
from datetime import timedelta
from ..utils import constants
import logging

_logger = logging.getLogger(__name__)

class report_service(models.Model):
    _name = 'time_tracking.report_service'
    _description = 'Servicio de informes de fichajes'
    
    def _get_records(self, employee_id, date_start, date_end):

        return self.env['time_tracking.record'].search([
            ('employee_id', '=', employee_id),
            ('date', '>=', date_start),
            ('date', '<=', date_end),
        ], order='date asc, time asc')


    def _generate_report(self, date_start, date_end, records):

        lines = []
        total_worked_hours = 0
        expected_hours = 0
        holiday_hours = 0
        extra_hours = 0

        # Agrupamos los fichajes por día
        records_by_day = {}
        for rec in records:
            records_by_day.setdefault(rec.date, []).append(rec)

        # Procesamos cada día
        for day, day_records in sorted(records_by_day.items()):
            worked_hours_day, detail = self._day_detail(day_records)

            # Calculamos horas trabajadas en festivo y las horas extra.
            if day in constants.FESTIVOS_2026:
                holiday_hours += worked_hours_day
            else:
                diff = worked_hours_day - constants.DURACION_JORNADA
                if diff > 0:
                    extra_hours += diff

            total_worked_hours += worked_hours_day

            # Añadimos la línea del día.
            lines.append({
                'date': day.strftime(constants.FORMATO_FECHA_INFORME), 
                'date_url': day.strftime(constants.FORMATO_FECHA_DATE), 
                'detail': detail,
                'hours': worked_hours_day,
            })

        # Calculamos horas esperadas (cogiendo de lunes a sábado que no sean festivos)
        day = date_start
        while day <= date_end:
            if day.weekday() < 6 and day not in constants.FESTIVOS_2026:
                expected_hours += constants.DURACION_JORNADA
            day += timedelta(days=1)

        hours_difference = round(total_worked_hours - expected_hours, 2)

        extra_holiday_value = round(extra_hours * constants.HORA_EXTRA + holiday_hours * constants.HORA_FESTIVO, 2)

        summary = {
            'total_worked_hours': total_worked_hours,
            'expected_hours': expected_hours,
            'hours_difference': hours_difference,
            'extra_hours': extra_hours,
            'holiday_hours': holiday_hours,
            'extra_holiday_value': extra_holiday_value,
        }

        return lines, summary


    def _day_detail(self, day_records):

        detail_parts = []
        break_time = False
        worked_hours = 0.0

        # Ordenamos por hora
        day_records = sorted(day_records, key=lambda day_record: day_record.time or 0.0)

        for day_record in day_records:
            hour_float = day_record.time
            hour_str = self._format_float_hour(hour_float)

            if day_record.type == 'exit':
                break_time = True
                detail_parts.append(f"- Hora salida: {hour_str} ")

            elif day_record.type == 'entry' and break_time:
                break_time = False
                detail_parts.append(f"/ Hora entrada: {hour_str} ")

            else:
                break_time = False
                detail_parts.append(f"Hora entrada: {hour_str} ")

            worked_hours += day_record.duration

        return round(worked_hours, 2), "".join(detail_parts)

    def _format_float_hour(self, value):
        hours = int(value)
        minutes = int(round((value - hours) * 60))
        return f"{hours:02d}:{minutes:02d}"
    
    def send_weekly_reports(self):

        today = fields.Date.today()
        end_date = today
        start_date = today - timedelta(days=6)

        employees = self.env['hr.employee'].search([])

        _logger.info("CRON: envío informes desde %s hasta %s", start_date, end_date)

        for employee in employees:
            try:
                if employee.name != "Administrator":
                    self.send_employee_report(employee, start_date, end_date)
                    _logger.info(f"Email enviado a {employee.private_email}")
                

            except Exception as e:
                _logger.exception("Error enviando informe a %s", employee.name)

    
    def send_employee_report(self, employee, date_start, date_end):

        email_to = employee.private_email

        records = self._get_records(employee.id, date_start, date_end)

        _logger.info("Empleado %s - registros: %s", employee.name, len(records))

        lines, summary = self._generate_report(date_start, date_end, records)

        html = self.env['ir.ui.view']._render_template(
            'time_tracking.email_report_template',
            {
                'doc': {
                    'employee_name': employee.name,
                    'date_start': date_start.strftime(constants.FORMATO_FECHA_INFORME),
                    'date_end': date_end.strftime(constants.FORMATO_FECHA_INFORME),
                    'lines': lines,
                    'total_worked_hours': summary['total_worked_hours'],
                    'expected_hours': summary['expected_hours'],
                    'hours_difference': summary['hours_difference'],
                    'extra_hours': summary['extra_hours'],
                    'holiday_hours': summary['holiday_hours'],
                    'extra_holiday_value': summary['extra_holiday_value'],
                }
            }
        )

        if not records:
            html = self.env['ir.ui.view']._render_template(
                'time_tracking.email_report_template_no_records',
                {
                    'doc': {
                        'employee_name': employee.name,
                        'date_start': date_start.strftime(constants.FORMATO_FECHA_INFORME),
                        'date_end': date_end.strftime(constants.FORMATO_FECHA_INFORME),
                    }
                }
            )
            
        if not employee.private_email:
            html = self.env['ir.ui.view']._render_template(
                'time_tracking.email_report_template_no_email_info',
                {
                    'doc': {
                        'employee_name': employee.name,
                    }
                }
            )   


        if not email_to:
            email_to = constants.EMAIL_ADMIN

        mail = self.env['mail.mail'].create({
            'subject': f'Informe fichajes {date_start.strftime(constants.FORMATO_FECHA_INFORME)} - {date_end.strftime(constants.FORMATO_FECHA_INFORME)}',
            'email_from': formataddr(('SuperDAM, S.L.', 'no_reply@superdam.es')),
            'email_to': email_to,
            'body_html': html,
        })

        _logger.info(f"FROM: {mail.email_from}")
        _logger.info(f"TO: {mail.email_to}")

        mail.send()

        _logger.info(f"Mail ID: {mail.id}")