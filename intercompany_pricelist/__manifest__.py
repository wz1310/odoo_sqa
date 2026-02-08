{
    'name': 'Intercompany Pricelist',
    'summary': """
        Intercompany Pricelist
        """,
    'version': '0.0.1',
    'category': 'sale,purchase',
    'author': 'La Jayuhni Yarsyah',
    'description': """
        Add Intercompany Pricelist
        When intercompany Order created, will use intercompany pricelist
    """,
    'depends': [
        'inter_company_rules',
    ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',

        'views/inter_company_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}