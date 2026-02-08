{
    'name': 'MIS Receive Report',
    'summary': """
        Receive Report from Good Receipt (PO-GR)""",
    'version': '1.0.0',
    'category': 'Report',
    "author": "MIS@SanQua",
    'description': """
        author : MIS@SanQua \n
        MIS Receive Report
    """,
    'depends': [
        'purchase'
    ],
    'data': [
        'report/mis_receive_report_view.xml',
        'report/mis_receive_report_without_invoice_view.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': False
}