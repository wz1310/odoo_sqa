# -*- coding: utf-8 -*-
{
    'name': "Sales Truck Item Status",

    'summary': """
            Sales Truck Item Status for Sanqua Odoo 13
            """,
    'description': """
        author : Rp. Bimantara \n
        Stock information about Galon & Dispenser in customer\n
    """,
    'author': "Port Cities",
    'website': "http://www.portcities.net",
    'category': 'Sale',
    'version': '0.1',
    'depends': ['sales_truck'],
    'data': [
        'security/access_right_sales_truck_status.xml',
        'security/ir.model.access.csv',
        'reports/security.xml',
        'wizard/wizard_view.xml',
        'views/res_partner_views.xml',
        'views/stock_picking_views.xml',
        'views/product_product_views.xml',
        'views/sale_order_truck_views.xml',
        'views/sales_truck_item_status.xml',
        'views/sale_truck_dispenser_status.xml',
        'views/stock_picking.xml',

        'reports/sale_truck_item_status_partner_report.xml',
        
    ],
    'installable': True,
    'application': False,
    'auto_install': False
}