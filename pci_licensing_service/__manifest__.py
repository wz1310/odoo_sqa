{
    'name': 'PCI - Licensing Service',
    'version': '13.0.1.0.0',
    'summary': 'Disable odoo licensing service',
    'description': """
        Forbidden used in real server. used only in training server.
    """,
    'category': 'Tools',
    'author': 'Portcities Ltd',
    'website': 'https://portcities.net',
    'license': 'LGPL-3',
    'contributors': [
        'Dhimas Yudangga A',
    ],
    'depends': [
        'web', 'mail',
    ],
    'data': [
        'data/update.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
