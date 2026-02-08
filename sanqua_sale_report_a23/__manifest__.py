{
    'name': 'Sanqua Sale Report A23',
    'summary': """
        Sanqua Sale Report A23
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Report',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Sanqua Sale Report A23 - Batavia Division Summary Sales Report for Sanqua Project
    """,
    'depends': [
        'sanqua_sale_report_a21'
    ],
    'data': [
        'security/ir.rule.xml',
        'security/ir.model.access.csv',

        'report/batavia_division_summary_sales_report_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}