# -*- coding: utf-8 -*-
{
    'name': "MIS Sanqua Print",

    'summary': """
        MIS Sanqua Print""",

    'description': """
        MIS Sanqua Print
    """,

    'author': "MIS@SanQua",
    'website': "https://www.sanquawater.co.id",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Report Print',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['sanqua_sale_flow', 'invoice_collection', 'settlement_request'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'report/report_settlementrequest.xml',
        'report/report_menu.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False
}
