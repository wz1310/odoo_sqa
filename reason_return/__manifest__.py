# -*- coding: utf-8 -*-
{
    'name': 'PCI Return of Goods',
    'category': 'Return Product',
    'version': '13.0.1.0.0',
    'depends': ['base','sales_truck','sales_team','approval_matrix','stock_picking_return_reason'],
    'author': 'Port Cities',
    'website': 'http://www.portcities.net',
    'summary': 'Extra feature in Sales',
    'sequence': 1,
    'description': """
Additional feature in Application Sales

v1.0
------
* New menu Form Return Goods in mainmenu Sales

    Author : AndreasC
    """,
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/picking_return_request.xml',
        'views/picking_return_request_line.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
