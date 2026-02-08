# -*- coding: utf-8 -*-
{
    'name': "MIS Bukti Potong",

    'summary': """
            MIS Bukti Potong
            """,
    'description': """MIS Bukti Potong""",
    'author': "MIS Sanqua",
    'category': 'Accounting',
    'version': '0.1',
    'depends': ['account','contacts','contact_flow'],
    'data': [
        # 'security/faktur_pajak_masuk_access_right.xml',
        'security/ir.model.access.csv',

        'views/mis_bukti_potong_view.xml',
        'wizard/export_bupot.xml',

        # 'wizard/reexport_efaktur.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}