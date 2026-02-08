{
    'name': 'Sanqua Sale Report A28',
    'summary': """
        Sanqua Sale Report A28
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Report',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Sanqua Sale Report A28 - Annually Summary Customer for Sanqua Project
    """,
    'depends': [
        'sanqua_sale_flow','sale_enterprise'
    ],
    'data': [
        'security/ir.rule.xml',
        'security/ir.model.access.csv',

        'report/annually_summary_customer_report_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}