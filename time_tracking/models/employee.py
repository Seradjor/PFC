from odoo import models, fields

class employee(models.Model):
    _inherit = 'hr.employee'

    id_time_tracking = fields.Char(string="ID fichaje")

    # Relación con time_tracking_record.
    records_ids = fields.One2many(
        'time_tracking.record',
        'employee_id',
        string="Fichajes"
    )

    # Constraints
    _sql_constraints = [('unique_id_time_tracking', 'unique(id_time_tracking)', 'El valor de id_time_tracking no se puede repetir')]
