{
    'name': 'Sanqua Galon Report M4',
    'summary': """
        Sanqua Galon Report M4
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Report Galon',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Sanqua Galon Report M4 for Sanqua Project
    """,
    'depends': [
        'sanqua_sale_flow','contact_flow'
    ],
    'data': [
        'security/ir.rule.xml',
        'security/ir.model.access.csv',
        'report/m4_report_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}