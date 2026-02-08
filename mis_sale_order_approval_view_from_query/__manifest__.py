{
    'name': 'MIS Res Partner',
    'summary': """
        This module used for Add driver type into res_partner""",
    'version': '0.0.1',
    'category': '',
    "author": "MIS@SanQua",
    'description': """
        This module used for Add driver type into res_partner
    """,
    'depends': ['contacts','sanqua_contact_competitor','contact_flow','sanqua_res_partner',
    'sales_truck_item_status','partner_credit_limit'
    ],
    'data': [
        'views/query_sale_order_view.xml'
        
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}