{
    'name': 'MIS Sales Inherit Forecast',
    'summary': """
        MIS Sales Inherit Forecast""",
    'version': '0.0.1',
    'category': 'Sales',
    'author': 'MIS@SanQua',
    'description': """
        MIS Sales Inherit Forecast
    """,
    'depends': ['sanqua_account_forecast_report'],
    'data': [
        'views/inherit_sales_forecast.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}