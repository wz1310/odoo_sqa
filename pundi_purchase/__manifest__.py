# -*- coding: utf-8 -*-
{
    'name': "Pundi Purchase",

    'summary': """
        Modul for Purchase Request and Purchase Order""",

    'description': """
        Long description of module's purpose
    """,

    'author': "R4Y Jr",
    'website': "rayci232@gmail.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','purchase_request','hr','purchase_request_department','purchase','purchase_stock','web_digital_sign'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/purchase_request.xml',
        'security/group.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/inherit_employee.xml',
        'views/inherit_purchase_request.xml',
        'views/inherit_purchase.xml',
        'report/purchase.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
