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
        help="If checked, this invoice has been archived and its journal entries reversed.",
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
            },
        }

    def action_do_archive(self):
        """Archive invoices: reverse posted ones, mark all as archived."""
        for move in self:
            if move.is_archived:
                continue

            if move.state == 'posted':
                reverse_wizard = self.env['account.move.reversal'].with_context(
                    active_model='account.move',
                    active_ids=move.ids,
                ).create({
                    'reason': _('Archived: %s') % move.name,
                    'refund_method': 'cancel',
                    'date': fields.Date.context_today(self),
                    'journal_id': move.journal_id.id,
                })

                reversal_result = reverse_wizard.reverse_moves()

                reversal_move = self.env['account.move']
                if reversal_result and reversal_result.get('res_id'):
                    reversal_move = self.env['account.move'].browse(reversal_result['res_id'])
                elif reversal_result and reversal_result.get('domain'):
                    reversal_move = self.env['account.move'].search(
                        reversal_result['domain'], limit=1, order='id desc'
                    )
                else:
                    reversal_move = self.env['account.move'].search([
                        ('reversed_entry_id', '=', move.id),
                    ], limit=1, order='id desc')

                if reversal_move:
                    move.archive_reversal_id = reversal_move.id
                    reversal_move.is_archived = True
                    _logger.info(
                        "Created reversal %s for archived invoice %s",
                        reversal_move.name, move.name
                    )

            move.is_archived = True

    def action_do_unarchive(self):
        """Unarchive invoices: reverse the reversal to restore journal entries."""
        for move in self:
            if not move.is_archived:
                continue

            if move.archive_reversal_id and move.archive_reversal_id.state == 'posted':
                reversal = move.archive_reversal_id

                reversal.is_archived = False

                re_reverse_wizard = self.env['account.move.reversal'].with_context(
                    active_model='account.move',
                    active_ids=reversal.ids,
                ).create({
                    'reason': _('Unarchived: %s') % move.name,
                    'refund_method': 'cancel',
                    'date': fields.Date.context_today(self),
                    'journal_id': reversal.journal_id.id,
                })
                re_reverse_wizard.reverse_moves()

                reversal.is_archived = True

            move.is_archived = False
            move.archive_reversal_id = False
