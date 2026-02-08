# -*- coding: utf-8 -*-
{
    'name': 'Sanqua Asset Management',
    'summary': """
        Asset Management for Sanqua""",
    'version': '13.0.1.0',
    'category': '',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Modify Asset Management for Sanqua
    """,
    'depends': [
        'account_asset','purchase_request','account_accountant'
    ],
    'data': [
        'views/account_views.xml',
        
        'wizard/invoice_asset_wizard_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True    
}