{
    'name': 'Sanqua Sale Report A17 and A18',
    'summary': """
        Sanqua Sale Report A17 and A18
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Report',
    "author": "Portcities Ltd",
    'description': """
        author : Reza Akbar Setyawan \n
        Sanqua Sale Report A17 and Report A18
    """,
    'depends': [
        'sanqua_sale_flow',
        'contact_flow',
        'sanqua_galon_report_1'
    ],
    'data': [
        'wizard/wizard_daily_report_oc_views.xml',
        'wizard/wizard_daily_report_a18_views.xml',
        'wizard/wizard_daily_report_a18_views_sot.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}