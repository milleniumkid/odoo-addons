# Copyright 2023 Yiğit Budak (https://github.com/yibudak)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# Copyright 2024 Ismail Cagan Yilmaz (https://github.com/milleniumkid)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class DeliverySendBatchEmail(models.TransientModel):
    _name = "delivery.send.batch.email"
    _description = "Send Batch Email to Customers"

    @api.model
    def send_batch_email(self):
        context = dict(self._context or {})
        active_ids = context.get("active_ids", []) or []
        pickings = self.env["stock.picking"].browse(active_ids)
        for record in self.web_progress_iter(
            pickings.filtered(lambda p: not p.mail_sent and p.shipping_number),
            msg="Sending emails...",
        ):
            try:
                record.button_mail_send()
            except Exception as e:
                self.env.cr.rollback()  # Roll back the transaction for this record
                record.message_post(body=f"Failed to send email: {e}")

        return {"type": "ir.actions.act_window_close"}
