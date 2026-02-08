{
    'name': 'PCI-SANQUA : Custom MRP',
    'version': '13.0.1.0.0',
    'category': 'Manufacturing',
    'author': 'Portcities Ltd',
    'website': 'http://www.portcities.net',
    'summary': """ Custom Manufacturing Module """,
    'description': """ 
        - Form view for Input Shift and Generated Production Report Per Shift.
        - Master Mesin and Generated Report 
    """,
    'depends': ['mrp'],
    'data': 
    [
    	'views/mrp_shift_views.xml',
        'views/mrp_mesin_views.xml',
        'views/mrp_production_views.xml',
        'views/mrp_production_group_views.xml',
        'security/rule.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': True    
}