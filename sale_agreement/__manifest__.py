{
    'name': 'Sale Agreement',
    'version': '13.0.1.0',
    'author': "Portcities Ltd",
    'category': 'Sales',
    'summary': """Sale Agreement""",
    'description': """
    Migrated By Alvin Adji from 12 to 13
    v 1.0
        author : Yusuf DW \n
        * Sale Agreement for sales targeting

    """,
    'depends': ['sale', 'purchase', 'partner_credit_limit', 'sale_credit_limit', 'merak_sale','sanqua_master_region','message_action_wizard','contact_flow'],
    'data' : [
        'data/ir_sequence_data.xml',
        'security/ir.model.access.csv',
        'security/rule.xml',
        'views/sale_agreement_views.xml',
        'views/sale_order_views.xml',
        'wizard/sale_agreement_cancel_wizard_views.xml'
    ],
    'installable': True,
    'application' : False,
    'auto_install' : False,
}
