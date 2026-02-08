{
    'name': 'Contact Competitor',
    'summary': """
        Contact Competitor
        for Sanqua Project""",
    'version': '0.0.1',
    'category': '',
    "author": "Rp. Bimantara",
    'description': """
        Add Model and inherits views to
        show contact competitor
    """,
    'depends': [
        'contacts','base'
    ],
    'data': [
    	'views/res_partner_views.xml',
    	'views/res_partner_competitor_views.xml',

        'security/competitor_access_right.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': True    
}