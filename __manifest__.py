{
    'name': 'Archive Posted Invoices',
    'version': '16.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Allow archiving invoices regardless of their state (including posted)',
    'description': """
        This module allows users to archive (set active=False) invoices
        even when they are in the 'posted' state.

        By default, Odoo prevents archiving posted journal entries/invoices.
        This module overrides that restriction and adds a convenient
        'Archive' / 'Unarchive' button on the invoice form view.

        Features:
        - Archive posted invoices (customer invoices & vendor bills)
        - Bulk archive/unarchive from the list view
        - Archive button directly on the invoice form
        - Respects access rights (only Billing users can archive)
    """,
    'author': 'Custom',
    'website': '',
    'license': 'LGPL-3',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
