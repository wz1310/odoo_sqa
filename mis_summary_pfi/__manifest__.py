{
    'name': 'Summary PFI',
    'summary': """
        Summary PFI
        Add summary invoice at PFI""",
    'version': '0.0.1',
    'category': 'Invoice',
    'author': 'MIS@SanQua',
    'description': """
        Summary PFI
        Add summary invoice at PFI
    """,
    'depends': [
        'account_accountant','pci_discounts_advance'
    ],
    'data': [
        'views/account_move.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}