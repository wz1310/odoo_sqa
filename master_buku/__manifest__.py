{
    'name': 'MY BOOK',
    'summary': """
        This module book""",
    'version': '0.0.1',
    'category': '',
    "author": "book",
    'description': """
        Module used for book
    """,
    'depends': ['base','mail'],
    'data': [
        'security/ir.model.access.csv',
        'books.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}