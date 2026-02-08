{
    'name': 'Operating Unit Sales Team',
    'version': '13.0.1.0.0',
    'author': "Portcities Ltd",
    'category': 'Base',
    'summary': """Operating Unit for Sales""",
    'description': """
    v 1.0
        author : Yusuf DW \n
        * Operating Unit for Sales \n
    Migrated from odoo12 to odoo13 by : \n
        author : Rofi SA
    """,
    'depends': ['operatingunit', 'sale'],
    'data' : [
        'views/crm_team_view.xml',
        'views/res_users_view.xml',
        'security/ir_rule.xml',
    ],
    'installable': True,
    'application' : False,
    'auto_install' : False,
}
