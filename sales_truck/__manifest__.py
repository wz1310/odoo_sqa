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
        * Adjustment Button Post Sale order truck\n
    """,
    'depends': ['product', 'stock', 'sale','fleet_transit_location', 'approval_matrix','sanqua_sale_flow','picking_to_invoice'],

    'data' : [
        'security/access_right.xml',
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml', 
        'views/product_template_views.xml',
        'views/product_product_views.xml',
        'views/sale_truck_item_views.xml',
        'views/sale_order_truck_views.xml',
        'views/sale_order_truck_dispanser_views.xml',
        'views/sale.xml',
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'application' : False,
    'auto_install' : False,
}
