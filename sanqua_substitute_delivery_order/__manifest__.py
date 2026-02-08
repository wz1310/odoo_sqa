# -*- coding: utf-8 -*-
{
    'name': 'PCI Substitute Goods in Delivery Order',
    'category': 'Substitute Product',
    'version': '13.0.1.0.0',
    'depends': [
        'base',
        'sale',
        'sales_team',
        'approval_matrix',
        'stock_picking_return_reason',
        'sanqua_sale_flow'],
    'author': 'Port Cities',
    'website': 'http://www.portcities.net',
    'summary': 'Extra feature in Transfers',
    'sequence': 1,
    'description': """
Additional feature in Application Inventory

v1.0
------
* New wizard menu form Substitute Items in menu Transfers
* New Sale Orders comes from Substitution of Goods in Delivery Order

    Author : AndreasC
    """,
    'data': [
        'views/sale_order_view.xml',
        'views/stock_picking_view.xml',
        'wizard/stock_picking_substitute.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
