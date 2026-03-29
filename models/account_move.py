from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_archived = fields.Boolean(
        string='Archived',
        default=False,
        copy=False,
        tracking=True,
    )
    archive_reversal_id = fields.Many2one(
        'account.move',
        string='Archive Reversal Entry',
        readonly=True,
        copy=False,
    )

    def action_open_archive_wizard(self):
        """Open the archive confirmation wizard."""
        return {
            'name': _('Archive Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'archive.invoice.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_move_ids': self.ids,
                'default_action_type': 'archive',
            },
        }

    def action_open_unarchive_wizard(self):
        """Open the unarchive confirmation wizard."""
        return {
            'name': _('Unarchive Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'archive.invoice.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_move_ids': self.ids,
                'default_action_type': 'unarchive',
            },
        }
