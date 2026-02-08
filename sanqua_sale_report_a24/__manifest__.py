{
    'name': 'Sanqua Sale Report A24',
    'summary': """
        Sanqua Sale Report A24
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Report',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Sanqua Sale Report A24 - Baverage Division Summary Sales Report for Sanqua Project
    """,
    'depends': [
        'sanqua_sale_report_a21'
    ],
    'data': [
        'security/ir.rule.xml',
        'security/ir.model.access.csv',

        'report/baverage_division_summary_sales_report_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}