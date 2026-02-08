{
    'name': 'Sale Credit Limit',
    'version': '13.0.1.0.0',
    'author': "Portcities Ltd",
    'category': 'Sales',
    'summary': """Sale Credit Limit""",
    'description': """
    v 1.0
        author : Yusuf DW \n
        * Approval system when customer have overdue,\n
        over limit, and no stock\n
    Migrated from odoo12 to odoo13 by\n
        author : Rofi SA
    """,
    'depends': ['sale_stock', 'partner_credit_limit', 'sales_team','merak_sale'],
    'data' : [
        'security/groups.xml',
        'security/ir.model.access.csv',
        
        'data/customer.group.csv',

        'views/customer_group.xml',
        'views/crm_team_views.xml',
        'views/sale_order_views.xml',
        'views/product_category_views.xml',
        'views/stock_picking_view.xml',
        'views/partner_pricelist_views.xml'
    ],
    'installable': True,
    'application' : False,
    'auto_install' : False,
}
