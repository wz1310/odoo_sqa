{
    'name': 'Sanqua Annual Forecast',
    'version': '',
    'author': "Sanquawater",
    'category': 'Sales',
    'summary': """Annual Forecast""",
    'description': """
Change Log

Version
-------------------------------
* Add new menu Report Forecast Penjualan and Tree view

    """,
    'depends': ['account',
                'product',
                'sale'
                ],
    'data' : [
        'security/ir.model.access.csv',
        # 'security/ir.rule.xml',
        'views/sale_annual_forecast_views.xml',
        'views/sale_annual_forecast_menus.xml',
    ],
    'installable': True,
    'application' : False,
    'auto_install' : False,
}
