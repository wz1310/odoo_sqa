# -*- coding: utf-8 -*-
{
    'name': "Delivery Lock Time",

    'summary': """
            Delivery Lock Time for Sanqua Odoo 13
            """,
    'description': """
        author : Rp. Bimantara \n
        Delivery Lock Time for customer delivery order\n
    """,
    'author': "Port Cities",
    'website': "http://www.portcities.net",
    'category': 'Sale',
    'version': '0.1',
    'depends': ['sanqua_sale_flow'],
    'data': [
        'data/ir.cron.xml',
        
        'views/res_partner_views.xml',
        'views/stock_picking_views.xml',
        'views/product_product_views.xml',
        'views/res_company_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False
}