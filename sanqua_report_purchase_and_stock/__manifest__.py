{
    'name': 'Sanqua Form Purchase order line and Stock picking line',
    'summary': """
        Sanqua Form Purchase order line and Stock picking line
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Purchase and Stock',
    "author": "Portcities Ltd",
    'description': """
        author : Reza Akbar Setyawan \n
        Sanqua Form Purchase order line and Stock picking line
    """,
    'depends': [
        'pci_discounts_advance',
        'order_global_discount',
        'purchase_request',
        'sanqua_budget',
        'sanqua_sale_flow',
        'stock'
    ],
    'data': [
        'views/purchase_order_line_views.xml',
        'views/stock_move_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}