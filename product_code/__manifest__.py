{
    'name': 'PCI-SANQUA : Product Code',
    'version': '13.0.1.0.0',
    'category': 'Manufacturing',
    'author': 'Portcities Ltd',
    'website': 'http://www.portcities.net',
    'summary': """ Custom Manufacturing Module """,
    
    'depends': ['mrp','inter_company_rules','pci_mrp', 'product'],
    'data': 
    [
        'views/mrp_production_views.xml', 
        'views/res_company_views.xml',
        'views/mrp_product_produce_views.xml',
        'views/product_template_views.xml', 
    ],
    'installable': True,
    'auto_install': False,
    'application': True    
}