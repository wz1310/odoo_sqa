{
    'name': 'Sanqua Galon Report Kas & Bank',
    'summary': """
        Sanqua Galon Report Kas & Bank
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Report Galon',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Sanqua Galon Report Kas & Bank for Sanqua Project
    """,
    'depends': [
        'sanqua_sale_flow','contact_flow','sanqua_galon_report_1','settlement_request'
    ],
    'data': [
        'security/ir.rule.xml',
        'security/ir.model.access.csv',
        'wizard/wizard_kasbank_report_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}