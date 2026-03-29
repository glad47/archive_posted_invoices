from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class ArchiveInvoiceWizard(models.TransientModel):
    _name = 'archive.invoice.wizard'
    _description = 'Archive / Unarchive Invoice Wizard'

    move_ids = fields.Many2many(
        'account.move',
        string='Invoices',
    )
    action_type = fields.Selection([
        ('archive', 'Archive'),
        ('unarchive', 'Unarchive'),
    ], string='Action', default='archive')

    def action_confirm(self):
        """Execute archive or unarchive based on action_type."""
        if not self.move_ids:
            raise UserError(_("No invoices selected."))

        if self.action_type == 'archive':
            self._do_archive()
        else:
            self._do_unarchive()

        title = _('Invoices Archived') if self.action_type == 'archive' else _('Invoices Unarchived')
        message = (
            _('%d invoice(s) archived. Reversal entries created.') % len(self.move_ids)
            if self.action_type == 'archive'
            else _('%d invoice(s) unarchived. Journal entries restored.') % len(self.move_ids)
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def _do_archive(self):
        """Archive invoices: reverse posted ones, mark all as archived."""
        for move in self.move_ids:
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

    def _do_unarchive(self):
        """Unarchive invoices: reverse the reversal to restore journal entries."""
        for move in self.move_ids:
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
