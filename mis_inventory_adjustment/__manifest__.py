# -*- coding: utf-8 -*-
{
    'name': "mis_inventory_adjustment",

    'summary': """mis_inventory_adjustment""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Sanqua Multi International",
    'website': "sanqua",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml'
    ]
}
