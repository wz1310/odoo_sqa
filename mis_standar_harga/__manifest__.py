{
    'name': 'Sanqua Standar Harga',
    'version': '',
    'author': "Sanquawater",
    'category': 'Sales',
    'summary': """Standar Harga""",
    'description': """
Change Log

Version
-------------------------------
* Add new menu Standar Harga

    """,
    'depends': [
                'product',
                'sale'
                ],
    'data' : [
        'security/ir.model.access.csv',
        # 'security/ir.rule.xml',
        'views/standar_harga.xml',
        'views/standar_harga_menus.xml',
    ],
    'installable': True,
    'application' : False,
    'auto_install' : False,
}
