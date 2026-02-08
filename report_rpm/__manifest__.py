{
    'name': 'Report Rencana Pembelian Material',
    'version': '13.0.1.0.0',
    'author': "Portcities Ltd",
    'category': 'Base',
    'summary': """Report RPM""",
    'description': """
    v 1.0
        author : Reno Kurnia Ramadhan Wastiko \n
        * Report Rencana Pembelian Material
    """,
    'depends': ['mrp_shift'],
    'data' : [
        'wizard/rpm_reporting_wizard_views.xml'
    ],
    'qweb': [
    ],
    'installable': True,
    'application' : False,
    'auto_install' : False,
}
