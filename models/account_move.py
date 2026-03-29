from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    # Odoo 16 account.move does NOT have an 'active' field by default
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help="If unchecked, the invoice will be hidden from default views.",
    )
    reversal_move_id = fields.Many2one(
        'account.move',
        string='Reversal Entry',
        readonly=True,
        copy=False,
        help="The reversal journal entry created when this invoice was archived.",
    )
    archived_by_module = fields.Boolean(
        string='Archived by Module',
        default=False,
        copy=False,
        help="Indicates this invoice was archived via the Archive Posted Invoices module.",
    )

    def _reverse_posted_moves(self):
        """Create reversal entries for all posted moves in self.

        This effectively cancels the accounting impact of the invoices
        by generating an equal-and-opposite journal entry for each one.
        Returns the created reversal moves.
        """
        reversal_moves = self.env['account.move']
        posted_moves = self.filtered(lambda m: m.state == 'posted')

        if not posted_moves:
            return reversal_moves

        for move in posted_moves:
            # Skip if already reversed by this module
            if move.reversal_move_id:
                _logger.info(
                    "Invoice %s already has a reversal entry %s, skipping.",
                    move.name, move.reversal_move_id.name
                )
                continue

            # Use Odoo's built-in reversal wizard logic
            reverse_wizard = self.env['account.move.reversal'].with_context(
                active_model='account.move',
                active_ids=move.ids,
            ).create({
                'reason': _('Archived: %s') % move.name,
                'refund_method': 'cancel',
                'date': fields.Date.context_today(self),
                'journal_id': move.journal_id.id,
            })

            # Execute the reversal
            reversal_result = reverse_wizard.reverse_moves()

            # Find the created reversal move
            reversal_move = self.env['account.move']
            if reversal_result and reversal_result.get('res_id'):
                reversal_move = self.env['account.move'].browse(reversal_result['res_id'])
            elif reversal_result and reversal_result.get('domain'):
                domain = reversal_result['domain']
                reversal_move = self.env['account.move'].search(domain, limit=1, order='id desc')
            else:
                reversal_move = self.env['account.move'].search([
                    ('reversed_entry_id', '=', move.id),
                ], limit=1, order='id desc')

            if reversal_move:
                move.write({'reversal_move_id': reversal_move.id})
                reversal_moves |= reversal_move
                _logger.info(
                    "Created reversal entry %s for invoice %s",
                    reversal_move.name, move.name
                )
            else:
                _logger.warning(
                    "Could not find reversal move for invoice %s", move.name
                )

        return reversal_moves

    def action_archive(self):
        """Archive invoices: reverse posted entries, then deactivate."""
        # Step 1: Reverse all posted moves
        reversal_moves = self._reverse_posted_moves()

        # Step 2: Mark as archived by module
        self.write({'archived_by_module': True})

        # Step 3: Deactivate the original invoices
        self.write({'active': False})

        # Step 4: Also archive the reversal entries
        if reversal_moves:
            reversal_moves.write({
                'archived_by_module': True,
                'active': False,
            })

        return True

    def action_unarchive(self):
        """Unarchive invoices: reactivate and reverse the reversal entry."""
        # Step 1: Reactivate the invoices
        self.write({'active': True})

        for move in self:
            if move.reversal_move_id:
                reversal = move.reversal_move_id

                # Reactivate the reversal entry first
                reversal.write({'active': True})

                # Reverse the reversal (restores original accounting)
                if reversal.state == 'posted':
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

                # Archive the old reversal entry
                reversal.write({'active': False})

                # Clear the link
                move.write({
                    'reversal_move_id': False,
                    'archived_by_module': False,
                })

        return True

    def toggle_active(self):
        """Override toggle_active to use our archive/unarchive logic."""
        to_archive = self.filtered(lambda r: r.active)
        to_unarchive = self.filtered(lambda r: not r.active)

        if to_archive:
            to_archive.action_archive()
        if to_unarchive:
            to_unarchive.action_unarchive()

        return True

    def action_archive_invoices(self):
        """Server action: Archive selected invoices from list view."""
        if not self:
            raise UserError(_("Please select at least one invoice to archive."))

        self.action_archive()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Invoices Archived'),
                'message': _(
                    '%d invoice(s) have been archived. '
                    'Reversal entries were created to clean journal movements.'
                ) % len(self),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_unarchive_invoices(self):
        """Server action: Unarchive selected invoices from list view."""
        if not self:
            raise UserError(_("Please select at least one invoice to unarchive."))

        self.action_unarchive()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Invoices Unarchived'),
                'message': _(
                    '%d invoice(s) have been unarchived. '
                    'Journal entries have been restored.'
                ) % len(self),
                'type': 'success',
                'sticky': False,
            }
        }
