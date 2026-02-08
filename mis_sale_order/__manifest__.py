{
    'name': 'MIS Sale Order Custom',
    'summary': """
        MIS Sale Order Column""",
    'version': '0.0.1',
    'category': 'Accounting',
    'author': 'MIS@SanQua',
    'description': """
        MIS Sale Order Column
    """,
    'depends': ['sanqua_sale_flow','sale_program_extend_free','picking_to_invoice','stock','sales_truck'
    ],
    'data': [
        'views/sale_order_view.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}