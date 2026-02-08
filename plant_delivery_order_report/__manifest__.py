{
    'name': 'WIM & PLANT SanQua Delivery Order Report',
    'summary': """
        Plant & WIM Delivery Order Report""",
    'version': '1.0.0',
    'category': 'Report',
    "author": "MIS@SanQua",
    'description': """
        author : Peter susanto \n
        Plant & WIM SanQua Delivery Order Report
    """,
    'depends': [
        'sanqua_sale_flow'
    ],
    'data': [
        'report/plant_delivery_order_report_view.xml',
        'report/plant_delivery_order_report_wo_invoice_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False
}