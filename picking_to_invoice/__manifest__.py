{
    'name': 'Picking To Invoice',
    'summary': """
        Picking To Invoice
        for Sanqua Project""",
    'version': '0.0.1',
    'category': '',
    "author": "Rp. Bimantara",
    'description': """
        Create an invoice from delivery order for Sanqua Project
    """,
    'depends': [
        'sanqua_sale_flow','invoice_lock'
    ],
    'data': [
        'views/stock_picking_views.xml',
        'views/account_move_views.xml',
        # 'report/delivery_order_report_views.xml',

        # 'security/ir.model.access.csv',
        # 'security/ir.rule.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}