# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.exceptions import UserError
from datetime import datetime
import csv
from io import StringIO


class TimeTracking(http.Controller):
    @http.route('/time_tracking/report/csv/<model("hr.employee"):employee>/<string:date_start>/<string:date_end>', type='http', auth='user')
    def time_tracking_report_csv(self, employee, date_start, date_end):

        # Otenemos datos a mostrar en informe.
        date_start, date_end, lines, summary = self._get_report_data(employee, date_start, date_end)

        # Construimos el fichero .csv
        output = StringIO()
        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)

        # 🔹 Cabecera del informe
        writer.writerow(["Informe de fichajes"])
        writer.writerow([f"Empleado: {employee.name}"])
        writer.writerow([f"Desde {date_start.strftime('%d/%m/%Y')} hasta {date_end.strftime('%d/%m/%Y')}"])

        # Línea en blanco
        writer.writerow([])

        # Cabecera tabla
        writer.writerow(["Fecha", "Detalle", "Horas"])

        # Líneas
        for line in lines:
            writer.writerow([
                line['date'],
                line['detail'],
                line['hours']
            ])

        # Línea en blanco
        writer.writerow([])

        # Resumen
        writer.writerow(["Resumen", "", ""])
        writer.writerow(["Total horas realizadas", "", summary['total_worked_hours']])
        writer.writerow(["Horas esperadas", "", summary['expected_hours']])
        writer.writerow(["Diferencia", "", summary['hours_difference']])
        writer.writerow(["Horas extra", "", summary['extra_hours']])
        writer.writerow(["Horas festivo", "", summary['holiday_hours']])
        writer.writerow(["Valor horas extra/festivo", "", summary['extra_holiday_value']])

        csv_content = output.getvalue()
        output.close()

        return request.make_response(
            csv_content,
            headers=[
                ('Content-Type', 'text/csv; charset=utf-8'),
                ('Content-Disposition', f'attachment; filename="informe_fichajes_{employee.name}.csv"')
            ]
        )


    def _get_report_data(self, employee, date_start, date_end):

        date_start = datetime.strptime(date_start, "%Y-%m-%d").date()
        date_end = datetime.strptime(date_end, "%Y-%m-%d").date()

        service = self._get_service()

        # Obtenemos registros.
        records = service._get_records(employee.id, date_start, date_end)

        if not records:
            raise UserError('Fichajes para el empleado y las fechas indicadas no encontrados.')

        lines, summary = service._generate_report(
            date_start,
            date_end,
            records
        )

        return date_start, date_end, lines, summary
    
    def _get_service(self):
        return request.env['time_tracking.report_service']