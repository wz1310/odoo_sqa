{
    'name': 'Inventory Report by Location | Stock Movement PDF and XLSX',
    'version': '18.0.0.1.0',
    'category': 'Inventory',
    'summary': 'Generate attractive inventory movement reports grouped by location',
    'author': 'Your Name/Sunray',
    'depends': ['stock', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/client_action.xml',
        'views/inventory_report_wizard_view.xml',
        'views/report_html_template.xml',
        'reports/report_action.xml',
        'reports/report_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'inventory_location_report/static/src/js/inventory_report_client.js',
            'inventory_location_report/static/src/xml/inventory_report_client.xml',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'OPL-1',
}