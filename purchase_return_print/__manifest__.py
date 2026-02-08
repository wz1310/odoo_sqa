{
    'name': 'Purchase Return Print',
    'summary': """
        Purchase Return Print
        """,
    'version': '0.0.1',
    'category': 'purchase,picking',
    'author': 'Portcities',
    'description': """
        Purchase Return Print
    """,
    'depends': [
        'sanqua_sale_flow','sanqua_print'
    ],
    'data': [
        'report/return.xml',
        'views/picking.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}