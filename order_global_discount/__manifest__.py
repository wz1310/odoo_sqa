# -*- coding: utf-8 -*-
{
    'name': 'Order Global Discount',
    'summary': """
        Purchase Order, Account Move""",
    'version': '13.0.1.0',
    'category': '',
    "author": "Portcities Ltd",
    'description': """
        Order Global Discount
    """,
    'depends': [
        'purchase','account','pci_discounts_advance'
    ],
    'data': [
        'views/purchase_view.xml',
        'views/account_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True    
}