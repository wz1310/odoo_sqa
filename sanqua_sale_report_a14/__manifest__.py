{
    'name': 'Sanqua Sale Report A14 LAPORAN CREDIT NOTE New',
    'summary': """
        Sanqua Sale Report A14 LAPORAN CREDIT NOTE
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Report',
    "author": "Portcities Ltd",
    'description': """
        author : Reza Akbar Setyawan \n
        Sanqua Sale Report A14 LAPORAN CREDIT NOTE
    """,
    'depends': [
        'sanqua_sale_flow',
        'contact_flow',
        'account'
    ],
    'data': [
        'security/ir.rule.xml',
        'security/ir.model.access.csv',
        'report/credit_note_report_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}