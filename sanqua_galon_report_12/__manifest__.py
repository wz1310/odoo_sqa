{
    'name': 'Sanqua Galon Report Amount Deposit Galon',
    'summary': """
        Sanqua Galon Report Amount Deposit Galon
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Report Galon',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Sanqua Galon Report Amount Deposit Galon for Sanqua Project
    """,
    'depends': [
        'sanqua_sale_flow','contact_flow','sanqua_galon_report_1'
    ],
    'data': [
        'security/ir.rule.xml',
        'security/ir.model.access.csv',
        'report/amount_deposit_galon_report_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}