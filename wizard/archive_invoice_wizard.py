from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ArchiveInvoiceWizard(models.TransientModel):
    _name = 'archive.invoice.wizard'
    _description = 'Archive Invoice Wizard'

    move_ids = fields.Many2many(
        'account.move',
        string='Invoices to Archive',
    )

    def action_confirm_archive(self):
        """Confirm and archive selected invoices."""
        if not self.move_ids:
            raise UserError(_("No invoices selected."))

        self.move_ids.action_do_archive()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Invoices Archived'),
                'message': _(
                    '%d invoice(s) archived. '
                    'Reversal entries created to clean journal movements.'
                ) % len(self.move_ids),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
