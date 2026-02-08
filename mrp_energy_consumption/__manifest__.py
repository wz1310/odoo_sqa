{
    'name': 'Energy Consumption',
    'version': '13.0.1.0.0',
    'author': 'Portcities Ltd.',
    'category': 'Manufacturing',
    'summary': """Energy Consumption""",
    'description': """
        Energy Consumption
    """,
    'depends': ['mrp','pci_mrp'],
    'data' : [
        'security/ir.rule.xml',
        'security/ir.model.access.csv',
        'views/mrp_kwh_view.xml',
    ],
    'installable': True,
    'application' : False,
    'auto_install' : False,
}
