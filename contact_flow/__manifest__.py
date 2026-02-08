{
    'name': 'Contact Flow',
    'summary': """
        Part A - New Customer""",
    'version': '0.0.1',
    'category': '',
    "author": "Rp. Bimantara",
    'description': """
        Part A - New Customer
    """,
    'depends': [
        'contacts','approval_matrix', 'web_many2one_reference','account','stock','delivery','sale','product','operatingunit',
    ],
    'data': [
        'data/ir_sequence.xml',
        'views/res_branch.xml',
    	'views/res_partner_views.xml',
    	'views/res_partner_document_field_views.xml',
    	'views/menu_views.xml',
    	'views/contact_change_request_views.xml',

        'views/res_company.xml',

        'data/action_server.xml',

        'security/contact_flow_access_right.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': True    
}