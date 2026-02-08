{
    'name': 'Sanqua Sale Report A21',
    'summary': """
        Sanqua Sale Report A21
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Report',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Sanqua Sale Report A21 - Global Division Summary Sales Report for Sanqua Project
    """,
    'depends': [
        'sanqua_sale_flow','sale_enterprise'
    ],
    'data': [
        'security/ir.rule.xml',
        'security/ir.model.access.csv',
        'views/sales_user_target_line_views.xml',
        'report/global_division_summary_sales_report_views.xml',
        'report/global_division_summary_sales_report_views_21.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}