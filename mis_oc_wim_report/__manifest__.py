{
    'name': 'OC WIM Report Realisasi',
    'summary': """
        This module is to show OC WIM Realisasi that expedition can take advance report """,
    'version': '0.0.1',
    'category': '',
    "author": "MIS@SanQua",
    'description': """
        This module is to show OC WIM Realisasi that expedition can take advance report
    """,
    'depends': [],
    'data': [
        'views/oc_wim_report.xml',
        'views/oc_wim_plant_report.xml',
        'views/oc_po_wim_report.xml',
        'security/oc_wim_access_right_v2.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}
