{
    'name': 'Sanqua Sale Report A12',
    'summary': """
        Sanqua Sale Report A12
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Report',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Sanqua Sale Report A12 - Laporan Performa Salesman for Sanqua Project
    """,
    'depends': [
        'sanqua_sale_flow','contact_flow'
    ],
    'data': [
        'security/ir.rule.xml',
        'security/ir.model.access.csv',

        'report/performa_salesman_report_views.xml',
        'wizard/wizard_performa_salesman_report_views.xml',
        'wizard/wizard_performa_salesman_report_excel_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}