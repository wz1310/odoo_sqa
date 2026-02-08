{
    'name': 'Sanqua Sale Report A1',
    'summary': """
        Sanqua Sale Report A1
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Report',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Sanqua Sale Report A1 for Sanqua Project
    """,
    'depends': [
        'sanqua_sale_flow','contact_flow'
    ],
    'data': [
        'security/ir.rule.xml',
        'security/ir.model.access.csv',
        'report/list_customer_report_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}