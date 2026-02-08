# coding: utf-8
{
    'name': 'Sanqua Res Partner',
    'version': '13.0.1.0',
    'author': 'Port Cities',
    'website': 'http://www.portcities.net',
    'category': 'Partner',
    'summary': 'Custom module res partner',
    'description': """
        add new menu input for evaluasi partner and add view in res partner
        created by reza
    """,
    'depends': [
        'contact_flow',
        ],
    'data': [
        'security/ir.model.access.csv',
        'views/evaluasi_supplier_views.xml',
        'views/res_partner_views.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}