# -*- coding: utf-8 -*-
{
    "name": "Filter Accounting Report",
    'version': '13.0.1.0',
    'summary': 'Accounting Report Filter',
    'website': 'http://portcities.net',
    'author': "Portcities Ltd",
    "sequence": 1,
    "category": "Accounting",
    "description": """
        v 1.0
        author : Dwiki Adnan F. \n
        * Add filter based on Operating Units on Accounting Reports
    """,
    'data': [
        'views/ringkasa_piutang_views.xml',
        'views/search_template_view.xml',
    ],
    "depends": [
        "account_reports", 
        "operatingunit"
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
