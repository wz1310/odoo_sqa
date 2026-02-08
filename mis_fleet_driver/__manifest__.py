{
    'name': 'MIS Fleet Driver',
    'summary': """
        This module used for Add driver into res_partner""",
    'version': '0.0.1',
    'category': '',
    "author": "MIS@SanQua",
    'description': """
        This module used for Add driver into res_partner
    """,
    'depends': ['fleet'
    ],
    'data': [
        'views/fleet_driver_view.xml',
        'views/fleet_vehicle_model_view.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}