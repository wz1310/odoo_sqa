{
    'name': 'Sanqua Sale Production Forecest Report',
    'summary': """
        Sanqua Sale Production Forecest Report
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Report',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Sanqua Sale Production Forecest Report for Sanqua Project
    """,
    'depends': [
        'sale','mrp'
    ],
    'data': [
        'security/ir.rule.xml',
        'security/ir.model.access.csv',
        
        'report/sale_production_forecest_report_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}