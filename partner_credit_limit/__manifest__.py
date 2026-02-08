{
    'name': 'Partner - Credit Limit, Bad Debt and Overdue',
    'version': '13.0.1.0.0',
    'category': 'Contact',
    'summary': 'Information Credit Limit, Bad Debt and Overdue',
    'author': "Portcities Ltd",
    'website': 'http://portcities.net',
    'description': """
    v 1.0
        author : Veri \n
        * Information Credit Limit, Bad Debt and Overdue \n 
    v 1.1
        author : Yusuf DW \n
        * Information Partner Pricelist Credit Limit\n
    migrated from odoo12 to odoo13 by :
        author : Rofi SA\n
    """,
    'depends': ['account_accountant',
                'contacts',
                'sale',
                'pci_discounts_advance',
                'account_reports'
                ],
    'data': [
        'security/ir.model.access.csv',
        'security/groups.xml',
        'views/black_list_view.xml',
        'views/partner_view.xml',
        'views/pricelist_discount.xml',
        'views/partner_pricelist_discount.xml',
        'views/partner_template.xml',
        'views/product_category_view.xml',
        'data/ir.cron.xml'
    ],
    'active': False,
    'installable': True,
    'application': False,
    'auto_install': False
}
