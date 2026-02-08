# pylint: disable=C0111,W0104
{
    'name': 'Compare Stock Report',
    'version': '13.0.1.0',
    'author': 'Portcities Ltd.',
    'category': 'Product',
    'summary': 'Custom report of stock product',
    'description': """
    v 1.0
        author : Reza \n

""",
    'depends': ['stock'],
    'data' : [
        'wizard/compare_stock_view.xml',
    ],
    'qweb': [],
    'active': False,
    'installable': True,
    'application' : False,
    'auto_install' : False,
}
