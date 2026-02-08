# -*- coding: utf-8 -*-
{
    'name': 'Settlement Request',
    'summary': """
        Settlement Request""",
    'version': '13.0.1.0',
    'category': '',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Settlement Request
    """,
    'depends': [
        'invoice_collection'
    ],
    'data': [
        'data/ir_sequence.xml',
        'views/settlement_request_views.xml',
        'views/collection_activity_views.xml',
        'views/account_journal_views.xml',

        'security/settlement_access_right.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': True    
}