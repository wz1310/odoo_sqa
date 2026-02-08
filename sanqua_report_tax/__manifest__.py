{
    'name': 'Sanqua Tax Report',
    'summary': """
        Sanqua Tax Report """,
    'version': '0.0.1',
    'category': 'Report',
    "author": "Portcities Ltd",
    'description': """
        Sanqua Tax Report
    """,
    'depends': [
        'base','account_accountant'
    ],
    'data': [
        'wizards/wizard_report_tax_07_view.xml',
        'wizards/wizard_report_tax_08_view.xml',
        'wizards/wizard_report_tax_09_view.xml',
        'wizards/wizard_report_tax_10_view.xml',
        'wizards/wizard_report_tax_11_view.xml',
        'wizards/wizard_report_tax_18_view.xml',
        'wizards/wizard_report_tax_01_view.xml',
        'wizards/wizard_report_tax_02_view.xml',
        'wizards/wizard_report_tax_03_view.xml',
        'wizards/wizard_report_tax_04_view.xml',
        'wizards/wizard_report_tax_05_view.xml',
        'wizards/wizard_report_tax_06_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False
}