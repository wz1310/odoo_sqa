{
    'name': 'Sanqua Contact Flow and Credit limit partner',
    'summary': """
        relation Contact Flow and Credit limit partner """,
    'version': '13.0.0.1',
    'category': 'Account',
    "author": "Portcities Ltd",
    'description': """
        update attributes invisible in tab division on partner
    """,
    'depends': [
        'contact_flow',
        'partner_credit_limit'
    ],
    'data': [
        'views/partner_view.xml'
        ],
    'installable': True,
    'auto_install': False,
    'application': False
}