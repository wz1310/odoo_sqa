# -*- coding: utf-8 -*-
{
    'name': "mis_product_company_sale",

    'summary': """
        Addons for check active company when open sale order and user 
        choose product just once with same product id""",

    'description': """
        Addons for check active company when open sale order and user 
        choose product just once with same product id
    """,

    'author': "MIS@SanQua",
    'website': "http://www.sanquawater.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','sanqua_sale_flow','sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
