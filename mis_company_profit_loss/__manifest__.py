# -*- coding: utf-8 -*-
{
    'name': "mis_company_profit_loss",

    'summary': """
        Title for Profit and loss report""",

    'description': """
        Title for Profit and loss report
    """,

    'author': "MIS@SanQua",
    'website': "http://www.sanquawater.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account_reports'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
