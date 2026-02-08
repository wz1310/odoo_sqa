{
    'name': 'Discount Target Support',
    'summary': """
        Discount Target Support
        for Sanqua Project""",
    'version': '13.0.1.0.0',
    'category': '',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Discount Target Support for Sanqua Project
    """,
    'depends': [
        'sale'
    ],
    'data': [
        'data/ir_sequence.xml',
    	'views/discount_target_support_master_views.xml',
    	'views/discount_target_support_customer_views.xml',
        'views/account_payment.xml',

        'report/discount_target_report_views.xml',
        'report/report_menu.xml',

        'security/discount_target_support_access_right.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': True    
}