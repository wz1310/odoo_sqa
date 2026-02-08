# -*- coding: utf-8 -*-
{
    'name': 'Accounting Collection',
    'summary': """
        Accounting Collection""",
    'version': '13.0.1.0',
    'category': '',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Accounting Collection
    """,
    'depends': [
        'account','sanqua_discount_target_support','contact_flow','pci_efaktur_13','approval_matrix','message_action_wizard'
    ],
    'data': [
        
        'security/collection_access_right.xml',
        'security/ir.model.access.csv',

        'data/ir_sequence.xml',
        'views/collection_activity_views.xml',
        'views/res_partner_views.xml',
        'views/res_company_views.xml',
        'views/menu_views.xml',

        'wizard/invoice_collection_wizard_views.xml',

        'report/invoice_position_report_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True    
}