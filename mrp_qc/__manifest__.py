{
    'name': 'Manufacturing Production QC',
    'version': '13.0.1.0.0',
    'author': 'Portcities Ltd.',
    'category': 'Manufacturing',
    'summary': """Quality Control Finish Goods""",
    'description': """
        Quality Control Finish Goods
    """,
    'depends': ['inward_quality', 'mrp_account_enterprise'],
    'data' : [
        'security/ir.model.access.csv',
        'views/picking_views.xml',
        'views/stock_location_views.xml',
        'views/mrp_views.xml',
        'views/master_reason_qc_views.xml',
        'wizard/quality_wiz_views.xml'
    ],
    'installable': True,
    'application' : False,
    'auto_install' : False,
}
