{
    'name': 'MRP SHIFT',
    'version': '13.0.1.0.0',
    'author': "Portcities Ltd",
    'category': 'Base',
    'summary': """MRP MPS for user""",
    'description': """
    v 1.0
        author : Reza Akbar \n
        * New module about MRP MPS user
    """,
    'depends': ['mrp_mps', 'approval_matrix', 'purchase_request'],
    'data' : [
        'data/ir_sequence.xml',
        'security/ir.model.access.csv',
        'security/ir_security.xml',
        'views/mrp_mps_templates.xml',
        'views/mrp_mps_menu_view.xml',
        'views/mrp_pbbh_views.xml',
        'views/mrp_rpb_views.xml',
        'views/mrp_rph_views.xml',
        # 'views/mrp_rpm_views.xml',
        'views/mrp_rpm_imp_views.xml',
        'views/stock_picking_views.xml',
        'views/stock_warehouse_views.xml',
        'views/stock_location_views.xml',
        'views/purchase_request_views.xml',
        'wizard/wizard_create_pbbh_views.xml',
        #'wizard/wizard_create_rpm_views.xml'
    ],
    'qweb': [
        "static/src/xml/qweb_templates.xml",
    ],
    'installable': True,
    'application' : False,
    'auto_install' : False,
}
