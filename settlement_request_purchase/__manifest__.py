# -*- coding: utf-8 -*-
{
    'name': 'Settlement Request Purchase',
    'summary': """
        Settlement Request Purchase""",
    'version': '13.0.1.0',
    'category': '',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Settlement Request
    """,
    'depends': [
        'invoice_collection','settlement_request'
    ],
    'data': [
        'security/settlement_access_right.xml',
        'security/ir.model.access.csv',

        'views/settlement_request_views.xml',

        
    ],
    'installable': True,
    'auto_install': False,
    'application': True    
}