# -*- coding: utf-8 -*-
{
    'name': 'Sale Carton',
    'summary': """
        Sale Carton Approvals""",
    'version': '13.0.1.0',
    'category': '',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Sale Carton Approvals
    """,
    'depends': [
        'sale','sanqua_sale_flow'
    ],
    'data': [
        'data/product_category.xml',

        'views/sale_order_views.xml',
        'views/product_category_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True    
}