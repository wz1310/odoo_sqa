{
    'name': 'Sales Report with Grouping Dropdown',
    'version': '18.0.1.0',
    'depends': ['sale', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/sales_report_wizard_view.xml',
        'views/report_html_template.xml',
        'views/client_action.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sale_sales_report/static/src/js/sales_report_client.js',
            'sale_sales_report/static/src/xml/sales_report_client.xml',
        ],
    },
}