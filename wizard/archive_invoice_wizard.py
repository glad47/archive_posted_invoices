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

        self.move_ids._do_archive()

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

    def action_confirm_unarchive(self):
        """Confirm and unarchive selected invoices."""
        if not self.move_ids:
            raise UserError(_("No invoices selected."))

        self.move_ids._do_unarchive()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Invoices Unarchived'),
                'message': _(
                    '%d invoice(s) unarchived. '
                    'Journal entries have been restored.'
                ) % len(self.move_ids),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
