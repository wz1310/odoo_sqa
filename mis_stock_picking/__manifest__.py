{
    'name': 'MIS Stock Picking',
    'summary': """
        This module used for extend from stock picking module """,
    'version': '0.0.1',
    'category': '',
    "author": "MIS@SanQua",
    'description': """
        Module for extend from stock picking
    """,
    'depends': [
        'stock','approval_matrix','delivery','sanqua_sale_flow','stock_picking_return_reason',
        'picking_to_invoice','mis_res_partner'
    ],
    'data': [
        'views/stock_picking_view.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}
