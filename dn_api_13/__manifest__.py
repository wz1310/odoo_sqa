# -*- coding: utf-8 -*-
{
    'name': "Odoo 13 Rest Api (Json)",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        1) Open odoo.conf
        2) Add 'dbfilter = dbname'.
        3) Restart odoo service.
    """,

    'author': "R4Y Jr",
    'website': "-",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Extra Tools',
    'price': 100,
    'currency': 'EUR',
    'version': '13.0',
    'support': 'rayci232@gmail.com',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/ir.model.access.csv',
        "data/ir_config_param.xml", 
        'views/res_users.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
