{
    'name': 'Sanqua Sale Report A8',
    'summary': """
        Sanqua Sale Report A8
        for Sanqua Project""",
    'version': '0.0.1',
    'category': 'Report',
    "author": "Portcities Ltd",
    'description': """
        author : Rp. Bimantara \n
        Sanqua Sale Report A8 - Laporan Perbandingan Penjualan Tahunan for Sanqua Project
    """,
    'depends': [
        'sanqua_sale_flow','contact_flow'
    ],
    'data': [
        'security/ir.rule.xml',
        'security/ir.model.access.csv',
        
        'wizard/wizard_yearly_sale_ratio_report_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False    
}