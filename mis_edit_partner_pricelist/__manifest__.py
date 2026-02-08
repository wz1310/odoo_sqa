{
    'name': 'Partner Pricelist Change Flow',
    'summary': """Partner Pricelist Change Flow""",
    'version': '0.0.1',
    'category': '',
    "author": "MIS@SANQUA",
    'description': """Partner Pricelist Change Flow""",
    'depends': ['approval_matrix', 'sale_credit_limit'
    ],
    'data': [
        'data/ir_sequence.xml',
        'views/pp_change_request_views.xml',
        'security/pp_flow_access_right.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': True    
}