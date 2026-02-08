{
    'name': 'Sales Truck',
    'version': '13.0.1.0.0',
    'author': 'Portcities Ltd.',
    'category': 'Sales',
    'summary': """Add relation to Location""",
    'description': """
    v 1.0
        author : Ipul \n
        * Add new model sales order truck\n
    v 1.0
        author : Rp. Bimantara \n
        * Serial Number references in Good Receipt\n
    """,
    'depends': ['stock','sanqua_sale_flow'],

    'data' : [
        'views/stock_picking_view.xml',
    ],
    'installable': True,
    'application' : False,
    'auto_install' : False,
}
