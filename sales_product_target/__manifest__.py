# -*- coding: utf-8 -*-
{
    'name': 'Sales Product Target',
    'summary': """
        Sales Product Target""",
    'version': '13.0.1.0',
    'category': 'Sales',
    "author": "Portcities Ltd",
    'website': 'https://www.portcities.net',
    'description': """
        author : Rp. Bimantara \n
        Sales Product Target for Sanqua
    """,
    'depends': [
        'sale','sale_credit_limit','mail','sanqua_master_region'
    ],
    'data': [
        'views/sales_product_target_views.xml',

        'security/sales_product_target_access_right.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': True    
}