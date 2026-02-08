{
    'name': 'Sale Approval Matrix',
    'summary': """
        Sale Approval Matrix
        """,
    'version': '0.0.1',
    'category': 'sale,approval',
    'author': 'La Jayuhni Yarsyah',
    'description': """
        Sale Order With Approval Matrix
    """,
    'depends': [
        'sale','approval_matrix','sale_management'
    ],
    'data': [
        'security/rules.xml',
        'views/sale.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}