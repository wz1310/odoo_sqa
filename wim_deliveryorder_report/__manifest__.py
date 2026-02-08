{
    'name': 'WIM SanQua Delivery Order Report',
    'summary': """
        MIS SanQua Delivery Order Report
        extend from A2 Delivery Orde""",
    'version': '1.0.0',
    'category': 'Report',
    "author": "MIS@SanQua",
    'description': """
        author : Peter susanto \n
        MIS SanQua Delivery Order Report
    """,
    'depends': [
        'sanqua_sale_flow'
    ],
    'data': [
        'security/ir.rule.xml',
        'report/wim_deliveryorder_report_view.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': False
}