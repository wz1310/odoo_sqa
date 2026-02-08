{
    'name': 'MIS Retur WIM SJ',
    'summary': """
        Add button to repair qty that not same between WIM SJ and Plant SJ """,
    'version': '0.0.1',
    'category': '',
    "author": "MIS@SanQua",
    'description': """
        Add button to repair qty that not same between WIM SJ and Plant SJ 
    """,
    'depends': [
        'stock','approval_matrix','delivery','sanqua_sale_flow'
    ],
    'data': [
        'views/stock_picking_view.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}