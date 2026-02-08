# -*- coding: utf-8 -*-
{
    'name': "sanqua_mis_report_energy_consumption",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        This report for dashboard view
    """,

    'author': "SanQua MIS Dept",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Report',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'report/report_energy_consumption.xml',
        'security/ir.rule.xml',
        'security/ir.model.access.csv',

    ],
    # only loaded in demonstration mode
    'installable': True,
    'auto_install': False,
    'application': False
}
