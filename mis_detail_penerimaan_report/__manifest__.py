{
    'name': 'MIS Detail Penerimaan',
    'summary': """
        MIS Detail Penerimaan
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Report',
    "author": "SANQUA",
    'description': """
        author : Andri \n
        MIS Detail Penerimaan for Sanqua Project
    """,
    'depends': ['base'
    ],
    'data': [
        'security/ir.rule.xml',
        'security/ir.model.access.csv',
        'report/list_detail_penerimaan_report_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}