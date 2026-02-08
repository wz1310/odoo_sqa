# -*- coding: utf-8 -*-
{
    'name': 'Purchase Request',
    'summary': """
        Purchase Request""",
    'version': '13.0.1.0',
    'category': '',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Purchase Request
    """,
    'depends': [
        'purchase','hr','approval_matrix','purchase_stock'
    ],
    'data': [
        
        'data/ir_sequence.xml',
        
        'views/approval_matrix.xml',
        'views/product.xml',
    	'views/purchase_request_views.xml',
    	'views/purchase_order_views.xml',
        
    	'wizard/purchase_request_to_order_views.xml',

        'security/puchase_request_access_right.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': True    
}