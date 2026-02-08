{
    'name': 'MIS General Ledger Additional Column',
    'summary': """
        MIS General Ledger Additional Column""",
    'version': '0.0.1',
    'category': 'Accounting',
    'author': 'MIS@SanQua',
    'description': """
        MIS General Ledger Additional Column
    """,
    'depends': [
        'account', 'picking_to_invoice'
    ],
    'data': [
        'views/account_move_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}