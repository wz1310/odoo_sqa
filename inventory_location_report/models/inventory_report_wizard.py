from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta

class InventoryLocationReportWizard(models.TransientModel):
    _name = 'inventory.location.report.wizard'
    _description = 'Wizard Laporan Inventaris per Lokasi'

    # Default value untuk tahun dan bulan (jika ingin mengikuti pola sales report)
    def _get_default_year(self):
        return str(datetime.now().year)

    def _get_default_month(self):
        return str(datetime.now().month)

    month = fields.Selection([
        ('1', 'Januari'), ('2', 'Februari'), ('3', 'Maret'), ('4', 'April'),
        ('5', 'Mei'), ('6', 'Juni'), ('7', 'Juli'), ('8', 'Agustus'),
        ('9', 'September'), ('10', 'Oktober'), ('11', 'November'), ('12', 'Desember')
    ], string='Bulan', required=True, default=_get_default_month)
    
    year = fields.Selection([
        (str(num), str(num)) for num in range(2020, 2031)
    ], string='Tahun', required=True, default=_get_default_year)

    # Filter berdasarkan lokasi (Stock Picking)
    location_ids = fields.Many2many(
        'stock.location', 
        string='Lokasi Sumber', 
        help="Pilih lokasi asal. Kosongkan untuk semua lokasi."
    )

    def action_view_onscreen(self):
        """Membuka laporan interaktif di layar (Client Action)"""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'inventory_location_report.client_action', # Harus sesuai dengan tag di JS
            'name': 'Inventory Report by Location',
            'context': {
                'month': self.month,
                'year': self.year,
                'location_ids': self.location_ids.ids if self.location_ids else [],
            }
        }

    def action_print_report(self):
        """Menghasilkan laporan format PDF"""
        self.ensure_one()
        
        # Kalkulasi rentang tanggal berdasarkan bulan/tahun yang dipilih
        date_start = datetime.strptime(f'{self.year}-{self.month}-01', '%Y-%m-%d').date()
        date_end = date_start + relativedelta(months=1, days=-1)
        
        # Jika lokasi kosong, ambil semua lokasi yang bertipe internal (atau sesuai kebutuhan)
        locations = self.location_ids or self.env['stock.location'].search([('usage', '=', 'internal')])
        
        data = {
            'form': {
                'date_start': date_start,
                'date_end': date_end,
                'location_ids': locations.ids,
                'month_name': dict(self._fields['month'].selection).get(self.month),
                'year': self.year,
            }
        }
        
        # Memanggil action report yang didefinisikan di XML
        return self.env.ref('inventory_location_report.action_report_inventory_location').report_action(self, data=data)