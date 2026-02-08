{
    'name': 'Sanqua Sale Report A13',
    'summary': """
        Sanqua Sale Report A13
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Report',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Sanqua Sale Report A13 - Laporan Target Penjualan Tahuan for Sanqua Project
    """,
    'depends': [
        'sanqua_sale_flow','contact_flow'
    ],
    'data': [
        'security/ir.rule.xml',
        'security/ir.model.access.csv',

        'report/annual_sales_target_report_views.xml',
        'wizard/wizard_annual_sales_target_report_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}