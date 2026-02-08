{
    'name': 'Operating Unit',
    'version': '13.0.1.0.0',
    'author': "Portcities Ltd",
    'category': 'Base',
    'summary': """Operating Unit""",
    'description': """
    v 1.0
        author : M Fitrohudin \n
        * New module about Operating Unit \n
    Migrated from odoo12 to odoo13 by \n
        author : Rofi SA
    """,
    'depends': ['base'],
    'data' : [
        'views/res_branch_view.xml',
        'views/res_users_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application' : False,
    'auto_install' : False,
}
