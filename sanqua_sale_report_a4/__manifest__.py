{
    'name': 'Sanqua Sale Report A4',
    'summary': """
        Sanqua Sale Report A4
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Report',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Sanqua Sale Report A4 - Laporan Performa Customer for Sanqua Project
    """,
    'depends': [
        'sanqua_sale_flow','contact_flow'
    ],
    'data': [
        'security/ir.rule.xml',
        'security/ir.model.access.csv',

        'report/performa_customer_report_views.xml',
        'wizard/wizard_performa_customer_report_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}