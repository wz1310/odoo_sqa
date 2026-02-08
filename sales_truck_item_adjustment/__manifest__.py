{
    'name': 'Sales Truck Item Adjusment',
    'summary': """
        Sales Truck Item Adjusment
        """,
    'version': '0.0.1',
    'category': 'sales truck,sales',
    'author': 'La Jayuhni Yarsyah',
    'description': """
        Sales Truck Adjusment Module
    """,
    'depends': [
        'sales_truck_item_status'
    ],
    'data': [
        'data/sequence.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/adjustment.xml',
        'views/partner_views.xml',
        'views/adjustment_galon.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}