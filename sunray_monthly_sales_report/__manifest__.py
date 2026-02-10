{
    'name': 'Monthly Sales Report by Salesperson | Sales Report Monthly | Sales reports PDF and XLSX',
    'version': '18.0.0.1.2',
    'category': 'Sales',
    'summary': 'Generate attractive monthly sales reports grouped by salesperson',
    'description': """
Monthly Sales Report by Salesperson
===================================
This module allows you to generate a detailed and visually appealing monthly sales report, grouped by salesperson.
    """,
    'author': 'Sunray Datalinks',
    'website': 'https://www.sunraydatalinks.com',
    'depends': ['sale_management', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/client_action.xml',
        'views/sales_report_wizard_view.xml',
        'views/report_html_template.xml',
        'reports/report_action.xml',
        'reports/report_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sunray_monthly_sales_report/static/src/js/monthly_sales_client.js',
            'sunray_monthly_sales_report/static/src/xml/monthly_sales_client.xml',
        ],
    },
    'images': ['static/description/banner.gif'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'OPL-1',
}
