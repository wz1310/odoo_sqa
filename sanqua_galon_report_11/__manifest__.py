{
    'name': 'Sanqua Galon Report Galon Daily',
    'summary': """
        Sanqua Galon Report Galon Daily
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Report Galon',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Sanqua Galon Report Galon Daily for Sanqua Project
    """,
    'depends': [
        'sanqua_sale_flow','contact_flow','sanqua_galon_report_1'
    ],
    'data': [
        'security/ir.rule.xml',
        'security/ir.model.access.csv',
        'report/galon_daily_report_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}