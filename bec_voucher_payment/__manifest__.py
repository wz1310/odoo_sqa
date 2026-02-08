# -*- coding: utf-8 -*-
{
    'name': "Bec Voucher Payment",

    'summary': """
        faliqulfikri@gmail.com""",

    'description': """
        khusus untuk Inagro 
    """,

    'author': "INAGRO",
    'website': "https://www.inagro.co.id/",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','num_to_words'],

    # always loaded
    'data': [
        'data/report_paperformat.xml',
        'data/data.xml',
        'data/res_groups.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/voucher_payment_views.xml',
        'views/invoice_views.xml',
        'report/voucher.xml',
        'report/voucher_report_views.xml',
    ],
    # only loaded in demonstration mode
    # 'css': ['static/src/css/style.css'],
    'demo': [
#         'demo/demo.xml',
    ],
}