{
    'name': 'MIS MIS Inherit PO Custom',
    'summary': """MIS Inherit PO""",
    'version': '0.0.1',
    'category': 'PO',
    'author': 'MIS@SanQua',
    'description': """MIS Inherit PO""",
    'depends': ['purchase_request','purchase','base'],
    'data': [
        'views/purchase_order_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}