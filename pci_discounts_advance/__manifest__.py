# -*- coding: utf-8 -*-
{
    'name': 'PCI Discounts Advance',
    'author': 'Portcities Ltd',
    'website': 'https://www.portcities.net',
    'version': '12.0.1.0',
    'summary': 'Sale, Purchase, Customer Invoice and Vendor Bill Discounts',
    'sequence': 1,
    'description': """
    v 1.0
        * Discount multi
    """,
    'category' : 'Accounting',
    'depends'  : ['purchase', 'account_accountant', 'sale'],
    'data'     : [
        'security/decimal.xml',
        'security/groups.xml',
        'views/sale_order_view.xml',
        'views/purchase_order_view.xml',
        'views/account_invoice_view.xml',
    ],
    'installable'   : True,
    'application'   : True,
    'auto_install'  : False
}