{
    'name': 'MIS Account Move',
    'summary': """
        MIS Account Move""",
    'version': '0.0.1',
    'category': 'Accounting',
    'author': 'MIS@SanQua',
    'description': """
        MIS Account Move
    """,
    'depends': ['account_accountant','pci_efaktur_13','mis_etax_invoice_merge'],
    'data': [
        'views/account_move_view.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}