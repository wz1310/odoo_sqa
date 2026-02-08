{
    'name': 'Sanqua Purchase Report',
    'summary': """
        Sanqua Purchase Report
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Report',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Sanqua Purchase Report for Sanqua Project
    """,
    'depends': [
        'purchase'
    ],
    'data': [
        'security/ir.model.access.csv',

        'report/purchase_report_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}