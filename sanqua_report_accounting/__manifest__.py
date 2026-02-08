{
    'name': 'Sanqua Form account move line',
    'summary': """
        account move line
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Account',
    "author": "Portcities Ltd",
    'description': """
        author : Reza Akbar Setyawan \n
        Sanqua Form account move line
    """,
    'depends': [
        'sanqua_sale_flow','contact_flow'
    ],
    'data': [
        'views/account_move_line_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}