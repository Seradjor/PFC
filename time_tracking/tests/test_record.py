from odoo.tests import TransactionCase
from datetime import date
import time

# Comprueba unicidad, búsquedas y rendimiento básico.
class test_record(TransactionCase):

    def setUp(self):
        super().setUp()
        self.record = self.env['time_tracking.record']

        self.employee = self.env['hr.employee'].create({'name': 'Empleado Test', 'id_time_tracking': '041459228921'})

    def test_record_id_sequence_per_employee(self):
        employee2 = self.env['hr.employee'].create({'name': 'Empleado Test 2', 'id_time_tracking': '041459228922'})

        self.create_record(self.employee.id, date(2026, 5, 6), 8.0, 'entry')
        record_employee = self.record.search([('employee_id', '=', self.employee.id)], order='id desc', limit=1)

        self.create_record(employee2.id, date(2026, 5, 6), 9.0, 'entry')
        record_employee2 = self.record.search([('employee_id', '=', employee2.id)], order='id desc', limit=1)

        self.assertEqual(record_employee.record_id, 1)
        self.assertEqual(record_employee2.record_id, 1)

    def test_duration_computation(self):

        # Fichajes realizados
        self.create_record(self.employee.id, date(2026, 5, 6), 9.0, 'entry')
        self.create_record(self.employee.id, date(2026, 5, 6), 14.0, 'exit')

        last_record = self.record.search([('employee_id', '=', self.employee.id)], order='id desc', limit=1)

        self.assertEqual(last_record.duration, 5.0)


    def test_nfc_register_sequence(self):

        # Fichajes realizados desde lector nfc
        self.record.nfc_register('041459228921')
        time.sleep(1)
        self.record.nfc_register('041459228921')
        time.sleep(1)
        self.record.nfc_register('041459228921')

        records = self.record.search([('employee_id', '=', self.employee.id)], order='id asc')

        self.assertEqual(records[0].type, 'entry')
        self.assertEqual(records[1].type, 'exit')
        self.assertEqual(records[2].type, 'entry')


    def test_nfc_duration(self):

        # Fichaje realizado manualmente previo a la ejecución del test
        self.create_record(self.employee.id, date(2026, 5, 6), 9.0, 'entry')

        # Fichajes realizados desde lector nfc
        self.record.nfc_register('041459228921')

        last_record = self.record.search([('employee_id', '=', self.employee.id)], order='id desc', limit=1)

        self.assertEqual(round(last_record.duration, 2), round ((self.record._default_time() - 9.0), 2))


    def test_nfc_record_type_after_day_without_exit(self):

        # Fichaje realizado manualmente el día anterior a la ejecución del test
        self.create_record(self.employee.id, date(2026, 5, 5), 15.0, 'entry')

        # Fichajes realizados desde lector nfc
        self.record.nfc_register('041459228921')

        last_record = self.record.search([('employee_id', '=', self.employee.id)], order='id desc', limit=1)

        self.assertEqual(last_record.type, "entry")
        

    def test_nfc_register_id_time_tracking_invalid(self):
        result = self.record.nfc_register('NO_EXISTE')

        self.assertEqual(result['status'], 'error')
        self.assertIn('Tarjeta no registrada', result['title'])


    def create_record(self, employee_id, date, time, type):
        self.record.create({'employee_id': employee_id, 'date': date, 'time': time, 'type': type})
