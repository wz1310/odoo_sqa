# -*- coding: utf-8 -*-
{
    'name': "Sanqua QC bahan baku",
    'summary': """Custom warehouse module for Sanqua""",
    'description': """
- Sanqua Stock QC
    """,
    'author': "Portcities",
    'website': "https://www.portcities.net",
    'category': 'Operations/Inventory',
    'version': '13.0.1',
    'depends': ['mrp_qc', 'inward_quality', 'purchase_request'],
    'data': [
        'data/data_stock.xml',
        # 'views/stock_picking_views.xml',
        'views/stock_picking_type_views.xml'
    ],
    'application': True,
    'installable': True,
}