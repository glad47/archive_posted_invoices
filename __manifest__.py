{
    'name': 'Archive Posted Invoices',
    'version': '16.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Allow archiving invoices regardless of their state (including posted)',
    'description': """
        This module allows users to archive (set active=False) invoices
        even when they are in the 'posted' state, and creates reversal
        entries to clean all journal movements.
    """,
    'author': 'Custom',
    'website': '',
    'license': 'LGPL-3',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
    ],
    'pre_init_hook': '_pre_init_add_active_field',
    'installable': True,
    'application': False,
    'auto_install': False,
}
