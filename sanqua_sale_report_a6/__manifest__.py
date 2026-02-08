{
    'name': 'Sanqua Sale Report A6',
    'summary': """
        Sanqua Sale Report A6
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Report',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Sanqua Sale Report A6 - Weekly Sale Ratio Report for Sanqua Project
    """,
    'depends': [
        'sanqua_sale_flow','contact_flow'
    ],
    'data': [
        'security/ir.rule.xml',
        'security/ir.model.access.csv',
        
        'wizard/wizard_weekly_sale_ratio_report_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}