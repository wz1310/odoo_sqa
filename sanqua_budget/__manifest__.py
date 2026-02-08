# -*- coding: utf-8 -*-
{
    'name': "Sanqua Budget",

    'summary': """
            Sanqua Budgeting for Sanqua Odoo 13
            """,
    'description': """
        author : Rp. Bimantara \n
        Sanqua Budgeting for Sanqua Odoo 13\n
    """,
    'author': "Port Cities",
    'website': "http://www.portcities.net",
    'category': 'Sale',
    'version': '0.1',
    'depends': ['account_budget'],
    'data': [
        'views/account_budget_views.xml',
        'views/purchase_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False
}