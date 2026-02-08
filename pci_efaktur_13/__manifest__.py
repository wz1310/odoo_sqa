# -*- coding: utf-8 -*-
{
    'name': "E-Faktur",

    'summary': """
            E-Faktur for Sanqua Odoo 13
            """,
    'description': """
        E-Faktur Menu\n
        Format : 010.000-16.00000001\n
        * 2 (dua) digit pertama adalah Kode Transaksi\n
        * 1 (satu) digit berikutnya adalah Kode Status\n
        * 3 (tiga) digit berikutnya adalah Kode Cabang\n
        * 2 (dua) digit pertama adalah Tahun Penerbitan\n
        * 8 (delapan) digit berikutnya adalah Nomor Urut\n
        v1.0
        ----
    """,
    'author': "Port Cities",
    'website': "http://www.portcities.net",
    'category': 'Accounting',
    'version': '0.1',
    'depends': ['account','contacts','purchase','contact_flow'],
    'data': [
        'security/etax_access_right.xml',
        'security/ir.model.access.csv',

        'views/etax_views.xml',
        'views/etax_series_views.xml',
        'views/res_partner_views.xml',
        'views/account_tax_views.xml',

        'wizard/reexport_efaktur.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}