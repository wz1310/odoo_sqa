from odoo import models, fields, api
from datetime import datetime

class SalesReportWizard(models.TransientModel):
    _name = 'sale.report.wizard'
    _description = 'Wizard Laporan Penjualan'

    month = fields.Selection([
        ('1', 'Januari'), ('2', 'Februari'), ('3', 'Maret'), ('4', 'April'),
        ('5', 'Mei'), ('6', 'Juni'), ('7', 'Juli'), ('8', 'Agustus'),
        ('9', 'September'), ('10', 'Oktober'), ('11', 'November'), ('12', 'Desember')
    ], string='Bulan', required=True, default=lambda self: str(datetime.now().month))
    
    year = fields.Selection([
        (str(num), str(num)) for num in range(2020, 2031)
    ], string='Tahun', required=True, default=lambda self: str(datetime.now().year))

    partner_ids = fields.Many2many('res.partner', string='Customers')

    def action_view_onscreen(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'sale_sales_report.sales_client_action',
            'name': 'Sales Report Analysis',
            'context': {
                'month': self.month,
                'year': self.year,
                'customer_ids': self.partner_ids.ids,
            }
        }