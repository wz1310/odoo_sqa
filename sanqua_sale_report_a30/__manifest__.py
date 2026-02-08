{
    'name': 'Sanqua Sale Report A30',
    'summary': """
        Sanqua Sale Report A30
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Report',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Sanqua Sale Report A30 - HARGA DASAR KONSUMEN WIM
    """,
    'depends': [
        'sanqua_sale_flow'
    ],
    'data': [
        'security/ir.rule.xml',
        'security/ir.model.access.csv',

        'report/harga_dasar_konsumen_report_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}