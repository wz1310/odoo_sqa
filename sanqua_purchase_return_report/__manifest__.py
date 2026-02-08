{
    'name': 'Sanqua Purchase Return Report',
    'summary': """
        Sanqua Purchase Return Report
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Report',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Sanqua Purchase Return Report for Sanqua Project
    """,
    'depends': [
        'purchase','stock'
    ],
    'data': [
        'security/ir.rule.xml',
        'security/ir.model.access.csv',

        'report/purchase_return_report_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}