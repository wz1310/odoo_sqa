{
    'name': 'Invoice Lock',
    'summary': """
        Invoice Lock
        Add new field lock into account.move""",
    'version': '0.0.1',
    'category': 'Inovice',
    'author': 'La Jayuhni Yarsyah',
    'description': """
        Add new field lock into account.move
        To Unlock need invoice manager to unlock
    """,
    'depends': [
        'account_accountant',
    ],
    'data': [
        'views/account_move.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}