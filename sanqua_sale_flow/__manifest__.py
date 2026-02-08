{
    'name': 'Sale Flow',
    'summary': """
        Sale Flow
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'sale,sanqua',
    "author": "La Jayuhni Yarsyah",
    'description': """
        Sales Flow from FRD Requirement
    """,
    'depends': [
        'sale_coupon',
        'partner_credit_limit', 
        'sale_credit_limit', 
        'operatingunit',
        'operatingunit_account',
        'operatingunit_sale',
        'sale_margin',
        'sale_agreement', 
        'inter_company_rules', 
        'multi_intercompany_procurement_order', 
        'operatingunit_warehouse', 
        
        'sale_approval_matrix',
        'pci_discounts_advance',
        'sales_team',
        'sanqua_master_region'
    ],
    'data': [
    	'data/approval.matrix.tag.xml',
        'data/sales_team.xml',
        'data/fleet_vehicle_model.xml',
        'data/order.pickup.method.csv',
        'data/ir_sequence.xml',
        'views/user.xml',

        'views/res_config_settings.xml',

        'views/stock_warehouse.xml',
    	'views/order_pickup_method.xml',
    	'views/partner.xml',
        'views/account_move.xml',
        'views/sales_team.xml',
    	'views/sale_order.xml',
        'views/stock_picking.xml',
        'views/stock_picking_type.xml',
        'views/purchase_order.xml',
        'views/stock_interco_move_line.xml',
        'views/sales_agreement_views.xml',
        'views/product_pricelist_views.xml',
        'views/product_category_views.xml',
        'views/stock_move_line_views.xml',
        'views/stock_production_lot_views.xml',

        'security/ir.module.category.csv',
        'security/res.groups.csv',
        'security/ir.model.access.csv',
        'security/ir.rule.xml',

        'wizard/sale_coupon_applied_wizard_views.xml',
        'wizard/sale_order_lock_wizard_views.xml',

        'views/report_deliveryslip.xml',
        'views/report_invoice.xml',

        'views/action_server.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'post_init_hook':'_auto_config_intercompany',
}