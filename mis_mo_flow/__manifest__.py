{
    'name': 'Mo Change Flow',
    'summary': """Mo Change Flow""",
    'version': '0.0.1',
    'category': '',
    "author": "MIS@SANQUA",
    'description': """Mo Change Flow""",
    'depends': [
        'mrp','approval_matrix', 'web_many2one_reference','stock','delivery',
    ],
    'data': [
        'data/ir_sequence.xml',
    	'views/mo_change_request_views.xml',
        'security/mo_flow_access_right.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': True    
}