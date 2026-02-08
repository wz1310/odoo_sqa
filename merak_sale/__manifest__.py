{
    'name': 'Sale MBP',
    'version': '12.0.1.0',
    'author': 'Port Cities',
    'category': 'Sale, Delivery Method',
    'summary': """""",
    'description': """
    v 1.0
        author : Reza Akbar \n
        * change delivery method per category\n
        * additional price per contact
        * feature configurasi payment team based on sales team
    Migration 12.0 to 13.0
    """
    ,
    'depends': ['sale_management'],
    'data' : [
        'views/crm_team.xml',
        'views/sale_order.xml',
        # 'report/report_sale_order.xml'
    ],
    'installable': True,
    'application' : False,
    'auto_install' : False,
}
