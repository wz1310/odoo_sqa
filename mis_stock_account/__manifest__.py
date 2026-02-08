# -*- coding: utf-8 -*-
{
    'name': "MIS Sanqua Stock Account",

    'summary': """
        Inherit from product.product to """,

    'description': """
        Long description of module's purpose
    """,

    'author': "MIS@SanQua",
    'website': "http://www.sanquawater.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Product',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'stock_account'
    ],

    # # always loaded
    # 'data': [
    #     'security/ir.model.access.csv',
    #     # 'views/views.xml',
    #     # 'views/templates.xml',
    # ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
