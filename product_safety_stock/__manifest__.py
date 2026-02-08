# -*- coding: utf-8 -*-
{
    'name': 'Product Safety Stock',
    'summary': """
        Product Safety Stock""",
    'version': '13.0.1.0',
    'category': 'Stock',
    "author": "Portcities Ltd",
    'description': """
        Product Safety Stock
    """,
    'depends': [
        'stock',
        'purchase',
        'product',
    ],
    'data': [
        'data/cron.xml',
        'views/res_config_view.xml',
        'views/product_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}