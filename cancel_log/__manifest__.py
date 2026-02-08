{
    'name': 'Cancel Log',
    'version': '13.0.1.0.0',
    'author': 'Portcities Ltd.',
    'category': 'Sales',
    'summary': """Add log when cancel SO""",
    'description': """
    v 1.0
        author : Yusuf DW \n
        * Add Popup reason when cancel SO\n
        * Add Log Messages when cancel SO\n
    migrated from odoo12 to odoo13 by :
        author : Rofi SA \n
    """,
    'depends': ['sale_management', 'account', 'stock'],
    'data' : [
        'views/sale_order_views.xml',
        'wizard/sale_log_cancel_views.xml',
        'views/account_payment_views.xml',
        'wizard/payment_log_cancel_views.xml',
        'views/picking_order_views.xml',
        'wizard/picking_log_cancel_views.xml',
    ],
    'installable': True,
    'application' : False,
    'auto_install' : False,
}
