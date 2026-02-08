{
    'name': 'Fleet Transit Location',
    'version': '13.0.1.0.0',
    'author': 'Portcities Ltd.',
    'category': 'Fleet',
    'summary': """Add relation to Location""",
    'description': """
    v 1.0
        author : Ipul \n
        * Add location in fleet\n
    """,
    'depends': ['stock', 'fleet'],
    'data' : [
        'views/fleet_vehicle_views.xml',
    ],
    'installable': True,
    'application' : False,
    'auto_install' : False,
}
