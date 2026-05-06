from odoo.tests import TransactionCase
from datetime import date
from ..utils import constants

class test_report_service(TransactionCase):

    def setUp(self):
        super().setUp()
        self.service = self.env['time_tracking.report_service']
        self.record = self.env['time_tracking.record']

        self.employee = self.env['hr.employee'].create({'name': 'Empleado Test'})


    def test_generate_report_normal_days(self):

        # Creamos fichajes días normales
        # Día 1
        self.create_record(self.employee.id, date(2026, 5, 6), 9.0, 'entry')
        self.create_record(self.employee.id, date(2026, 5, 6), 13.0, 'exit')
        self.create_record(self.employee.id, date(2026, 5, 6), 15.0, 'entry')
        self.create_record(self.employee.id, date(2026, 5, 6), 17.0, 'exit')

        # Día 2
        self.create_record(self.employee.id, date(2026, 5, 7), 9.0, 'entry')
        self.create_record(self.employee.id, date(2026, 5, 7), 13.0, 'exit')
        self.create_record(self.employee.id, date(2026, 5, 7), 15.0, 'entry')
        self.create_record(self.employee.id, date(2026, 5, 7), 17.0, 'exit')

        records = self.record.search([('employee_id', '=', self.employee.id)])

        lines, summary = self.service._generate_report(date(2026, 5, 6), date(2026, 5, 7), records)

        self.assertEqual(len(lines), 2)

        self.assertEqual(lines[0]['hours'], constants.WORKDAY_DURATION)

        self.assertEqual(summary['total_worked_hours'], constants.WORKDAY_DURATION*2) 

        self.assertEqual(summary['expected_hours'], constants.WORKDAY_DURATION*2) 

        self.assertEqual(summary['extra_hours'], 0.0) 


    def test_generate_report_with_extra_hours(self):

        # Creamos fichajes días normales
        # Día 1
        self.create_record(self.employee.id, date(2026, 5, 6), 9.0, 'entry')
        self.create_record(self.employee.id, date(2026, 5, 6), 13.0, 'exit')
        self.create_record(self.employee.id, date(2026, 5, 6), 15.0, 'entry')
        self.create_record(self.employee.id, date(2026, 5, 6), 18.0, 'exit')

        # Día 2
        self.create_record(self.employee.id, date(2026, 5, 7), 9.0, 'entry')
        self.create_record(self.employee.id, date(2026, 5, 7), 13.0, 'exit')
        self.create_record(self.employee.id, date(2026, 5, 7), 15.0, 'entry')
        self.create_record(self.employee.id, date(2026, 5, 7), 18.0, 'exit')

        records = self.record.search([('employee_id', '=', self.employee.id)])

        lines, summary = self.service._generate_report(date(2026, 5, 6), date(2026, 5, 7), records)

        self.assertEqual(len(lines), 2)

        self.assertEqual(lines[0]['hours'], 7.0)

        self.assertEqual(summary['total_worked_hours'], 14.0) 

        self.assertEqual(summary['expected_hours'], 12.0) 

        self.assertEqual(summary['extra_hours'], 2.0) 

        self.assertEqual(summary['extra_holiday_value'], 2.0*constants.OVERTIME_HOUR) 


    def test_generate_report_with_holiday_day(self):

        # Creamos fichajes días normales
        # Día 1
        self.create_record(self.employee.id, date(2026, 4, 30), 9.0, 'entry')
        self.create_record(self.employee.id, date(2026, 4, 30), 13.0, 'exit')
        self.create_record(self.employee.id, date(2026, 4, 30), 15.0, 'entry')
        self.create_record(self.employee.id, date(2026, 4, 30), 17.0, 'exit')

        # Día 2
        self.create_record(self.employee.id, date(2026, 5, 1), 9.0, 'entry')
        self.create_record(self.employee.id, date(2026, 5, 1), 13.0, 'exit')
        self.create_record(self.employee.id, date(2026, 5, 1), 15.0, 'entry')
        self.create_record(self.employee.id, date(2026, 5, 1), 17.0, 'exit')

        records = self.record.search([('employee_id', '=', self.employee.id)])

        lines, summary = self.service._generate_report(date(2026, 5, 6), date(2026, 5, 7), records)

        self.assertEqual(len(lines), 2)

        self.assertEqual(lines[1]['hours'], 6.00)

        self.assertEqual(summary['total_worked_hours'], 12.0) 

        self.assertEqual(summary['expected_hours'], 12.0) 

        self.assertEqual(summary['holiday_hours'], 6.0) 

        self.assertEqual(summary['extra_holiday_value'], 6.0*constants.HOLIDAY_HOUR) 


    def create_record(self, employee_id, date, time, type):
        self.record.create({'employee_id': employee_id, 'date': date, 'time': time, 'type': type})
