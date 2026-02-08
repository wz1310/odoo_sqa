# -*- coding: utf-8 -*-
{
    'name': "Partner Scheduler",

    'summary': """
            Partner Scheduler for delete data res.partner in state draft and waiting approval
            """,
    'description': """
        author : Rp. Bimantara \n
        Delivery Lock Time for customer delivery order\n
    """,
    'author': "Port Cities",
    'website': "http://www.portcities.net",
    'category': 'Contact',
    'version': '0.1',
    'depends': ['contact_flow'],
    'data': [
        'data/ir.cron.xml',
        'views/res_company_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False
}