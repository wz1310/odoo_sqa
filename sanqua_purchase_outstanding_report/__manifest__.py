{
    'name': 'Sanqua Purchase Outstanding Report',
    'summary': """
        Sanqua Purchase Outstanding Report
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Report',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Sanqua Purchase Outstanding Report for Sanqua Project
    """,
    'depends': [
        'purchase'
    ],
    'data': [
        'wizard/wizard_outstanding_report_views.xml',
        'wizard/wizard_purchase_raw_material_report_views.xml',
        'wizard/wizard_riwayat_report_views.xml',
        'wizard/wizard_purchase_return_report_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}