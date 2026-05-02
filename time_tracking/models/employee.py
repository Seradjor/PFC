from odoo import models, fields
from odoo.exceptions import UserError
import requests
import random

class employee(models.Model):
    _inherit = 'hr.employee'

    id_time_tracking = fields.Char(string="ID fichaje")

    # Relación con time_tracking_record.
    records_ids = fields.One2many(
        'time_tracking.record',
        'employee_id',
        string="Fichajes"
    )

    # 041442864386

    # Constraints
    _sql_constraints = [('unique_id_time_tracking', 'unique(id_time_tracking)', 'El valor de id_time_tracking no se puede repetir')]

    def action_write_card(self):
        self.ensure_one()

        if not self.id_time_tracking:
            raise UserError("Indique primero un ID de tarjeta.")

        return {
            "type": "ir.actions.act_window",
            "name": "Grabación tarjeta",
            "res_model": "time_tracking.nfc_write",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_employee_id": self.id,
                "default_code_to_write": self.id_time_tracking,
            }
        }


    def action_generate_new_id(self):
        self.ensure_one()

        # Generar ID de 12 dígitos
        new_id = ''.join(str(random.randint(0, 9)) for _ in range(12))

        # Validar que no exista en otro empleado
        exists = self.search([
            ('id_time_tracking', '=', new_id),
            ('id', '!=', self.id)
        ], limit=1)

        if exists:
            raise UserError("Se ha generado un ID duplicado. Inténtalo de nuevo.")

        # Guardar el nuevo ID
        self.id_time_tracking = new_id

        return True