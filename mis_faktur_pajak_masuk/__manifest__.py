# -*- coding: utf-8 -*-
{
    'name': "MIS Faktur Pajak Masukan",

    'summary': """
            MIS Faktur Pajak Masukan
            """,
    'description': """MIS Faktur Pajak Masukan
    """,
    'author': "MIS Sanqua",
    'category': 'Accounting',
    'version': '0.1',
    'depends': ['account','contacts','contact_flow'],
    'data': [
        'security/mis_faktur_pajak_masuk_access.xml',
        'security/ir.model.access.csv',

        'views/mis_faktur_pajak_masuk_view.xml',
        'wizard/export_fpm.xml',

        # 'wizard/reexport_efaktur.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}