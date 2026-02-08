{
    'name': 'Operating Unit Account',
    'version': '13.0.1.0.0',
    'author': "Portcities Ltd",
    'category': 'Base',
    'summary': """Operating Unit for Account""",
    'description': """
    v 1.0
        author :Reza Akbar \n
        * Operating Unit for Account
    Migrated from odoo12 to odoo13 by
        author : Rofi SA
    """,
    'depends': ['operatingunit',
                'stock_account',
                'sale',
                'analytic'
                # 'stock_mark_delivered' Modul BELUM DIMIGRASI
                ],
    'data' : [
        'views/account_journal_view.xml',
        'views/res_users_view.xml',
        'security/ir_rule.xml',
        'views/stock_picking_type_view.xml',
        'views/stock_picking_view.xml',
        'views/sale_order_view.xml'
    ],
    'installable': True,
    'application' : False,
    'auto_install' : False,
}
