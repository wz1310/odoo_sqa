{
    'name': 'Sanqua Sale Report A11',
    'summary': """
        Sanqua Sale Report A11
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Report',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Sanqua Sale Report A11 - Piutang Sales for Sanqua Project
    """,
    'depends': [
        'sanqua_sale_flow','account'
    ],
    'data': [
        'security/ir.rule.xml',
        'security/ir.model.access.csv',

        'report/outstanding_receiveable_report_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}