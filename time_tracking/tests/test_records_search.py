from odoo.tests import TransactionCase
from odoo.exceptions import UserError
from datetime import date, timedelta


class test_records_search(TransactionCase):

    def setUp(self):
        super().setUp()
        self.employee = self.env['hr.employee'].create({'name': 'Empleado Test'})
        self.records_search = self.env['time_tracking.records_search']


    def test_date_start_after_today_raises_error(self):
        tomorrow = date.today() + timedelta(days=1)

        records_search = self.records_search.create({'employee_id': self.employee.id, 'date_start': tomorrow, 'date_end': tomorrow})

        with self.assertRaises(UserError) as e:
            records_search.action_search_records()

        self.assertEqual(str(e.exception), "Día inicial no puede ser posterior al día de hoy.")


    def test_date_end_before_date_start_message(self):
        records_search = self.records_search.create({'employee_id': self.employee.id, 'date_start': date(2026, 4, 10), 'date_end': date(2026, 4, 5)})

        with self.assertRaises(UserError) as e:
            records_search.action_search_records()

        self.assertEqual(str(e.exception), "Día final no puede ser anterior al día inicial.")

