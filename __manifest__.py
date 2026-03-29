{
    'name': 'Archive Posted Invoices',
    'version': '16.0.2.0.0',
    'category': 'Accounting',
    'summary': 'Archive posted invoices with automatic journal reversal',
    'description': """
        Archive invoices regardless of state (including posted).
        Automatically creates reversal entries to clean journal movements.
        Uses cancel/reverse approach - no active field hacks.
    """,
    'author': 'Custom',
    'license': 'LGPL-3',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/archive_invoice_wizard_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
