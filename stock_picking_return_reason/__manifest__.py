{
    'name': 'Stock Picking Return Reason',
    'summary': """
        Add Reason for stock.picking and stock.return.picking """,
    'version': '0.0.1',
    'category': '',
    "author": "Rp. Bimantara",
    'description': """
        Add Reason for stock.picking and stock.return.picking
    """,
    'depends': [
        'stock','approval_matrix','delivery','sanqua_sale_flow'
    ],
    'data': [
        'wizard/wizard_intercompany_return.xml',
    	'views/stock_picking_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True    
}