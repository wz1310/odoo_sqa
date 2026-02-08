{
    'name': 'Master Region',
    'summary': """
        Master Region
        for Sanqua Project""",
    'version': '0.0.1',
    'category': '',
    "author": "Rp. Bimantara",
    'description': """
        Master Region for Sanqua Project
    """,
    'depends': [
        'contacts','sale','stock','contact_flow'
    ],
    'data': [
        'security/region_access_right.xml',

        'views/region_region_views.xml',
        'views/region_master.xml',
    	
    	'views/region_group_views.xml',
    	'views/region_discount_views.xml',
    	'views/res_partner_views.xml',

        
        # 'security/res.groups.csv',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': True    
}