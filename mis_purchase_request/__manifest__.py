{
    'name': 'MIS MIS Inherit PR Custom',
    'summary': """MIS Inherit PR""",
    'version': '0.0.1',
    'category': 'PR',
    'author': 'MIS@SanQua',
    'description': """MIS Inherit PR""",
    'depends': ['purchase_request','base'],
    'data': [
        'views/purchase_request_view.xml',
        # 'views/asset.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}