{
    'name': 'MIS ETax Invoice Merge',
    'summary': """
        MIS ETax Invoice Merge additional features""",
    'version': '0.0.1',
    'category': 'Accounting',
    'author': 'MIS@SanQua',
    'description': """
        MIS ETax Invoice Merge additional features
    """,
    'depends': ['pci_efaktur_13','picking_to_invoice','stock','sanqua_print'],
    'data': [
        'views/account_move_commercial_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}