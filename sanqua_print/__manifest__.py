{
    'name': 'Sanqua Print Out',
    'version': '13.0.1.0.0',
    'category': 'Contact',
    'summary': 'Print out report for sanqua',
    'author': "Portcities Ltd",
    'website': 'http://portcities.net',
    'description': """
    v 1.0
        author : Rp. Bimantara \n
        * Print out report for sanqua \n 
    """,
    'depends': ['sanqua_sale_flow','sales_truck'],
    'data': [
        'views/res_company_views.xml',
        'views/sale_order_truck_views.xml',
        'views/account_move.xml',
        
        'report/report_deliveryslip.xml',
        'report/report_invoice.xml',
        'report/report_invoice_return.xml',
        'report/report_invoice_collection_unpaid.xml',
        'report/report_invoice_collection_paid.xml',
        'report/report_invoice_tax_deduction_receipt.xml',
        'report/report_invoice_tax_receipt.xml',
        'report/report_purchaseorder.xml',
        'report/report_purchaseorders.xml',
        'report/report_purchasereturn.xml',
        'report/report_payment.xml',
        #'report/report_receiveitems.xml',
        'report/report_receiveitems_template.xml',
        'report/report_internal_transfer.xml',
        'report/report_internal_transfers.xml',
        'report/report_sales_order_truck.xml',
        'report/report_menu.xml',

        'security/ir.model.access.csv'
    ],
    'installable': True,
    'application': False,
    'auto_install': False
}
