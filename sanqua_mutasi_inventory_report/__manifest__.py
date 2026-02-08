# -*- coding: utf-8 -*-
{
    "name": 'Sanqua - Mutasi Inventory Report',
    "summary": "Wizard for Generate Mutasi Inventory Report",
    "version": "13.0.1.0.1",
    "author": "PCS Engineer-Portcities Ltd",
    "website": "https://portcities.net",
    "category": "Reporting",
    "depends": ['stock','account'],
    "license": "LGPL-3",
    "data": [
        'data/product_classification_data.xml',
        'security/ir.model.access.csv',
        'wizard/wizard_mutasi_inventory.py_view.xml',
        'wizard/wizard_mutasi_inventory.py_view_without_value.xml'
    ],
    "installable": True,
    "application": True,
}