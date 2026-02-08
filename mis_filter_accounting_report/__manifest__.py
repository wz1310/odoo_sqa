# -*- coding: utf-8 -*-
{
    'name': "mis_filter_accounting_report",

    'summary': """
        This module for inherit from filter_accounting_report/account_report""",

    'description': """
        Long description of module's purpose
    """,

    'author': "MIS@SanQua",
    'website': "http://www.sanquawater.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ["account_reports", 
        "operatingunit","filter_accounting_report","sanqua_report_warehouse"],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False
}
