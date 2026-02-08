# -*- coding: utf-8 -*-
{
    'name': 'PCI Sale Promotion',
    'category': 'Sale Promotion',
    'version': '13.0.1.0.0',
    'depends': ['base','sale','sales_team','stock','approval_matrix','contact_flow','sanqua_sale_flow'],
    'author': 'Port Cities Indonesia',
    'website': 'http://www.portcities.net',
    'summary': 'Extra feature in Sales',
    'sequence': 1,
    'description': """
Additional feature in Application Sales

v1.0
------
* Request product sample to new leads
* Request product sample to events
* Internal memo for outgoing product from warehouse 

Author : AndreasC
    """,
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/sale_order_view.xml',
        'views/sale_order_line_view.xml',
        'views/sale_order_promotion.xml',
        'views/sale_order_promotion_line.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
