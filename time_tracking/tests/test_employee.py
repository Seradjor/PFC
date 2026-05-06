from odoo.tests import TransactionCase
from odoo.exceptions import UserError
from unittest.mock import patch


class test_employee(TransactionCase):

    def setUp(self):
        super().setUp()

        self.employee = self.env['hr.employee'].create({'name': 'Empleado Test', 'id_time_tracking': False})


    def test_generate_new_id_Ok(self):
        self.employee.action_generate_new_id()

        self.assertTrue(self.employee.id_time_tracking)
        self.assertEqual(len(self.employee.id_time_tracking), 12)


    def test_generate_new_id_duplicate(self):
        # Creamos otro empleado con un ID
        employee2 = self.employee.create({'name': 'Otro Empleado', 'id_time_tracking': '041459228921'})

        # Simulamos que random genera ese mismo ID
        with patch('random.randint', side_effect=[int(x) for x in "041459228921"]):
            with self.assertRaises(UserError):
                self.employee.action_generate_new_id()

        # Si volvemos a generar nuevo id, este será diferente y no dará error.
        self.employee.action_generate_new_id()
        self.assertNotEqual(self.employee.id_time_tracking, "041459228921")

