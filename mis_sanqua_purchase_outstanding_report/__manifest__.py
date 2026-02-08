{
    'name': 'Sanqua Purchase Outstanding Report',
    'summary': """
        Sanqua Purchase Outstanding Report
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Report',
    "author": "Portcities Ltd",
    'description': """
        author : MIS SANQUA \n
        Inherit sanqua_purchase_outstanding_report_v1
    """,
    'depends': [
        'sanqua_purchase_outstanding_report'
    ],
    'data': [
        'inherit_wizard_purchase_raw_material_report_views.xml','inherit_wizard_purchase_return_report_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}