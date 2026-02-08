{
    'name': 'Multi Intercompany Procurement Order',
    'summary': """
        Multi Intercompany Procurement Order
        """,
    'version': '0.0.1',
    'category': 'sales,multi company',
    "author": "jayu@portcities.net",
    'description': """
        Multi Intercompany Procurement Order
    """,
    'depends': [
        'web', 'contacts', 'sale','stock','account','purchase', 'inter_company_rules', 'intercompany_pricelist',
    ],
    'data': [
    	'views/sale.xml',
    ],
    'post_init_hook':'_auto_config_intercompany',
    'installable': True,
    'auto_install': False,
    'application': True    
}