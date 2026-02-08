# -*- coding: utf-8 -*-
{
    'name': 'Product Receive Tolerance',
    'summary': """
        Product Receive Tolerance""",
    'version': '13.0.1.0',
    'category': '',
    "author": "Portcities Ltd",
    'description': """
        Product Receive Tolerance
    """,
    'depends': [
        'purchase','product','stock'
    ],
    'data': [
        'views/product_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}