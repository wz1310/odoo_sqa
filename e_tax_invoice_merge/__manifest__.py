# -*- coding: utf-8 -*-
{
    'name': "E-Faktur Invoice Merger",

    'summary': """
            E-Faktur Invoice Merger for Sanqua Odoo 13
            """,
    'description': """
        E-Faktur Invoice Merger Menu\n
    """,
    'author': "Port Cities",
    'website': "http://www.portcities.net",
    'category': 'Accounting',
    'version': '0.1',
    'depends': ['pci_efaktur_13'],
    'data': [
        'data/ir_sequence.xml',
        'data/server.xml',

        'security/etax_invoice_merge_access_right.xml',
        'security/ir.model.access.csv',
        
        'views/account_move_commercial_views.xml',
        'views/reexport_faktur_views.xml',

        'report/invoice_commercial_report_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}