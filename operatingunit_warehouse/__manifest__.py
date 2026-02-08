{
    'name': 'Operating Unit Warehouse',
    'version': '13.0.1.0.0',
    'author': "Portcities Ltd",
    'category': 'Base',
    'summary': """Operating Unit in Warehouse""",
    'description': """
    v 1.0
        author : Yusuf DW \n
        * Restrict Warehouse based on Operating Unit
    Migrated from odoo12 to odoo13 by:
        author : Rofi SA
    """,
    'depends': ['operatingunit', 'stock_account'],
    'data' : [
        'views/res_users_view.xml',
        'views/stock_warehouse_view.xml',
        'security/ir_rule.xml',
    ],
    'installable': True,
    'application' : False,
    'auto_install' : False,
}
