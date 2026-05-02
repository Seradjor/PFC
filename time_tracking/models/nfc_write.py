from odoo import models, fields, api
from odoo.exceptions import UserError
import requests

class nfc_write(models.TransientModel):
    _name = "time_tracking.nfc_write"
    _description = "Asistente para grabar tarjeta NFC"

    employee_id = fields.Many2one("hr.employee", string="Empleado")
    code_to_write = fields.Char(string="Código a grabar")

    def action_confirm_write(self):
        """Llamado al pulsar Aceptar en el popup."""
        self.ensure_one()

        try:
            response = requests.post(
                "http://192.168.1.11:5001/write_card",
                json={"code": self.code_to_write},
                timeout=20
            )
            data = response.json()

            if data.get("status") != "ok":
                raise UserError(f"Error grabando tarjeta: {data.get('message')}")

        except Exception as e:
            raise UserError(f"No se pudo comunicar con el lector NFC: {e}")

        # Notificación final
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Tarjeta grabada",
                "message": f"ID {self.code_to_write} grabado correctamente.",
                "type": "success",
                "next": {
                    "type": "ir.actions.act_window_close"
                }
            }
        }
