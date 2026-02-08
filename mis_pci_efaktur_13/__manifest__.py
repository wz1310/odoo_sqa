# -*- coding: utf-8 -*-
{
    'name': "mis_pci_efaktur_13",

    'summary': """
        This module for inherit from pci_efaktur_13""",

    'description': """
        The purpose of this module is inherited from pci_efaktur_13
    """,

    'author': "MIS@SanQua",
    'website': "http://www.sanquawater.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['pci_efaktur_13'],

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
