{
    'name': 'Sanqua Delivery Order Report',
    'summary': """
        Sanqua Delivery Order Report
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Report',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Sanqua Delivery Order Report for Sanqua Project
    """,
    'depends': [
        'sanqua_sale_flow'
    ],
    'data': [
        'security/ir.rule.xml',
        'security/ir.model.access.csv',

        'report/realization_order_report_views.xml',
        'report/realization_order_delivered_report_views.xml',
        'report/realization_order_driver_report_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}