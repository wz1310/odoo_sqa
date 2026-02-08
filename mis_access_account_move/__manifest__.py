{
    'name': 'MIS Access Account Move',
    'summary': """
        MIS Account Move""",
    'version': '0.0.1',
    'category': 'Accounting',
    'author': 'MIS@SanQua',
    'description': """
        MIS Access Account Move
    """,
    'depends': ['account_accountant','mis_etax_invoice_merge'],
    'data': [
        'views/account_move_view.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}