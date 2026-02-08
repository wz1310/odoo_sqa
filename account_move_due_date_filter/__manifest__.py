# -*- coding: utf-8 -*-
{
    'name': 'Account Move Due Date Filter',
    'summary': """
        Account Move Due Date Filter""",
    'version': '13.0.1.0',
    'category': '',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Account Move Due Date Filter
    """,
    'depends': [
        'account'
    ],
    'data': [
        'security/due_date_access_right.xml',
        'security/ir.model.access.csv',
        'views/account_move_due_date_filter_views.xml',

        'report/report_invoice_due_date.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True    
}