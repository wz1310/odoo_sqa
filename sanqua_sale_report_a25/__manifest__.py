{
    'name': 'Sanqua Sale Report A25',
    'summary': """
        Sanqua Sale Report A25
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Report',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Sanqua Sale Report A25 - Sale Summary SKU
    """,
    'depends': [
        'sanqua_sale_flow'
    ],
    'data': [
        'security/ir.rule.xml',
        'security/ir.model.access.csv',

        'report/sale_summary_sku_report_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}