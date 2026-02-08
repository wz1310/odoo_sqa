{
    'name': 'Sanqua Sale Report A27',
    'summary': """
        Sanqua Sale Report A27
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Report',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Sanqua Sale Report A27 - Summary Customer DO
    """,
    'depends': [
        'sanqua_sale_flow'
    ],
    'data': [
        'security/ir.rule.xml',
        'security/ir.model.access.csv',

        'report/summary_customer_do_report_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}