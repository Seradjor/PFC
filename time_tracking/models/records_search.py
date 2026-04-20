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

        # Comprobamos que hayan fichajes.
        self._get_records(self.employee_id.id, self.date_start, self.date_end)

        # Redirección al controller
        url = f"/time_tracking/report/{self.employee_id.id}/{self.date_start}/{self.date_end}"

        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'self',
        }

    def _get_records(self, employee_id, date_start, date_end):
        Record = self.env['time_tracking.record']
        domain = [
            ('employee_id', '=', employee_id),
            ('date', '>=', date_start),
            ('date', '<=', date_end),
        ]
        records = Record.search(domain, order='date asc, time asc')

        if not records:
            raise UserError('Fichajes para el empleado y las fechas indicadas no encontrados.')

        return records

    def _generate_report(self, records):

        lines = []
        total_worked_hours = 0
        expected_hours = 0
        holiday_hours = 0
        extra_hours = 0

        # Agrupamos los fichajes por día
        records_by_day = {}
        for record in records:
            records_by_day.setdefault(record.date, []).append(record)

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
                'date': day.strftime(constants.FORMATO_FECHA), # Formateo la fecha a tipo String y le doy el formato deseado.
                'detail': detail,
                'hours': worked_hours_day,
            })

        # Calculamos horas esperadas (cogiendo de lunes a sábado que no sean festivos)
        day = self.date_start
        while day <= self.date_end:
            if day.weekday() < 6 and day not in constants.FESTIVOS_2026:
                expected_hours += constants.DURACION_JORNADA
            day += timedelta(days=1)

        hours_difference = total_worked_hours - expected_hours

        extra_holiday_value = (
            extra_hours * constants.HORA_EXTRA +
            holiday_hours * constants.HORA_FESTIVO
        )

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
        entry_hour = None    

        # Ordenamos por hora
        day_records = sorted(day_records, key=lambda day_record: day_record.time or 0.0)

        for day_record in day_records:
            record_type = day_record.type
            hour_float = day_record.time
            hour_str = self._format_float_hour(hour_float)

            if record_type == 'exit':
                break_time = True
                detail_parts.append(f"- Hora salida: {hour_str} ")

                if entry_hour is not None:
                    worked_hours += max(0.0, hour_float - entry_hour)
                    entry_hour = None

            elif record_type == 'entry' and break_time:
                break_time = False
                detail_parts.append(f"/ Hora entrada: {hour_str} ")
                entry_hour = hour_float

            else:
                break_time = False
                detail_parts.append(f"Hora entrada: {hour_str} ")
                entry_hour = hour_float

        return worked_hours, "".join(detail_parts)


    def _format_float_hour(self, value):
        hours = int(value)
        minutes = int(round((value - hours) * 60))
        return f"{hours:02d}:{minutes:02d}"
