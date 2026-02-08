{
    'name': 'MIS Sanqua Sale Report A9',
    'summary': """
        Sanqua Sale Report A9
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Report',
    "author": "MIS SANQUA",
    'description': """
        author : MIS \n
        Sanqua MIS Report A9
    """,
    'depends': [
        'sanqua_sale_flow',
        'contact_flow',
        'sanqua_galon_report_1'
    ],
    'data': [
        'wizard/wizard_mis_A9_report_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}