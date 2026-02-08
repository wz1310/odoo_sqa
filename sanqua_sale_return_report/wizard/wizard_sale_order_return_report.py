# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
import logging
_logger = logging.getLogger(__name__)
import base64
from datetime import date
from io import BytesIO
from calendar import monthrange
from odoo.exceptions import ValidationError
try:
	from odoo.tools.misc import xlsxwriter
except ImportError:
	import xlsxwriter

class WizardSaleOrderReturnReport(models.TransientModel):
	_name = 'wizard.sale.order.return.report'
	_description = 'Wizard Sale Order Return Report'

	start_date = fields.Date(string='Start Date', required=True)
	end_date = fields.Date(string='End Date', required=True)
	company_id = fields.Many2one('res.company',
								 string='Company',
								 required=True)
	name = fields.Char(string="Filename", readonly=True)
	data_file = fields.Binary(string="File", readonly=True)
	customer_ids = fields.Many2many('res.partner', string="Customer", domain=[('customer','=',True)])
	product_ids = fields.Many2many('product.product',string='Products')
	group_by = fields.Selection([('product','Product'),('customer','Customer')],string='Group By', default='product')
	
	def button_print(self):
		data = self._get_data_sale()
		if not data :
			raise ValidationError(_("Data Tidak ditemukan, Silahkan coba dengan Filter lainnya"))
		return self.generate_excel(data)

	def _get_data_sale(self):
		customer_filter = ""
		if self.customer_ids:
			if len(self.customer_ids) == 1:
				data_tuple = "(%s)" % self.customer_ids.id
			else:
				data_tuple = tuple(self.customer_ids.ids)
			customer_filter = ("AND so.partner_id IN %s") % (str(data_tuple))

		product_filter = ""
		# test 123  56
		if self.product_ids:
			if len(self.product_ids) == 1:
				product_tuple = "(%s)" % self.product_ids.id
			else:
				product_tuple = tuple(self.product_ids.ids)
			product_filter = (" AND so_line.product_id IN %s") % (str(product_tuple))
		query = """
			SELECT  
				rp.name AS partner_name, 
				sp.name AS so_name, 
				so.date_order AS date_order, 
				pt.name AS product_name, 
				so_line.product_uom_qty AS kts,
				so_line.price_unit AS price_unit, 
 				so_line.qty_delivered AS total_kts,
 				(so_line.product_uom_qty - so_line.qty_delivered) AS saldo_kts,
				'-' AS status,
				sp.no_sj_vendor as no_sj_vendor,
				so_line.name as deskripsi,
				-- sp.no_sj_wim as no_sj_wim,
				REPLACE(sp.origin, 'Return of ', '') as no_sj_wim,
				sp.date_received as tgl_terima,
 				CASE WHEN sp.origin LIKE %s THEN -1 * sm.product_uom_qty ELSE sm.product_uom_qty END as qty_terima,
				cur.name as mata_uang,
				uom.name as satuan, so_line.discount as diskon,
				sp.return_reason as alasan,
				sp.return_type as tipe_retur
			FROM sale_order so
			LEFT JOIN sale_order_line so_line ON so_line.order_id = so.id
			JOIN res_partner rp ON rp.id = so.partner_id
			JOIN product_product pp ON pp.id = so_line.product_id
			JOIN product_template pt ON pt.id = pp.product_tmpl_id
			LEFT JOIN stock_move sm ON sm.sale_line_id = so_line.id
			LEFT JOIN stock_picking sp ON sm.picking_id = sp.id
			LEFT JOIN res_currency cur ON so_line.currency_id = cur.id
			LEFT JOIN uom_uom uom ON so_line.product_uom = uom.id
			WHERE sp.origin LIKE %s AND sp.state = 'done' AND so.company_id = %s AND sp.date_received BETWEEN %s AND %s """ + customer_filter+product_filter + """
			ORDER BY sp.date_received, pt.name, rp.name, so.id;
		"""
		self._cr.execute(query, ('Return %', 'Return %', self.company_id.id,self.start_date,self.end_date))
		res = self._cr.dictfetchall()
		return res

	def generate_excel(self,data):
		""" Generate excel based from sale.order record. """
		fp = BytesIO()
		workbook = xlsxwriter.Workbook(fp)
		worksheet = workbook.add_worksheet()
		
		# ========== Format ==============
		header_table = workbook.add_format({'bold':True,'valign':'vcenter','align':'center','text_wrap':True})
		header_table.set_font_size(12)
		header_table.set_font_name('Times New Roman')
		header_partner_table = workbook.add_format({'bold':True,'valign':'vcenter','align':'left','text_wrap':True})
		header_partner_table.set_font_size(10)
		header_partner_table.set_font_name('Times New Roman')

		body_table = workbook.add_format()
		body_table.set_align('left')
		body_table.set_align('vcenter')
		body_table.set_font_size(10)
		body_table.set_font_name('Times New Roman')

		body_right_table = workbook.add_format()
		body_right_table.set_align('right')
		body_right_table.set_align('vcenter')
		body_right_table.set_font_size(10)
		body_right_table.set_font_name('Times New Roman')
		body_right_table.set_num_format('#,##0.00')

		header_right_table = workbook.add_format({'bold':True,'valign':'vcenter','align':'center','text_wrap':True})
		header_right_table.set_align('right')
		header_right_table.set_align('vcenter')
		header_right_table.set_font_size(12)
		header_right_table.set_font_name('Times New Roman')
		header_right_table.set_num_format('#,##0.00')

		# ========== Header ==============
		worksheet.merge_range('A2:H2',self.company_id.name,header_table)
		worksheet.merge_range('A3:H3','Laporan Retur Penjualan ',header_table)
		worksheet.merge_range('A4:H4',(_('Dari %s s/d %s') % (self.start_date.strftime("%d %b %Y"),self.end_date.strftime("%d %b %Y"))),header_table)

		# worksheet.merge_range('B6:G6', 'No. Pesanan',header_table)
		# worksheet.write('C7', 'Tgl Pesan',header_table)
		# worksheet.merge_range('E7:G7', 'Deskripsi Barang',header_table)
		# worksheet.write('I7', 'Qty. Pesan',header_table)
		# worksheet.write('K7', 'Harga Satuan',header_table)
		# worksheet.write('M7', 'Total Qty. Diterima',header_table)
		# worksheet.write('O7', 'Saldo Qty.',header_table)
		# worksheet.merge_range('Q7:R7', 'Status Pesanan',header_table)

# No barang	NO PO	NO SJ customer	Tanggal SJ	Desk Barang	Nama Pembeli	Kts	Satuan	Harga satuan	Jml Valas	Mata uang	Biaya rata2

		row = 6
		worksheet.write(row,0, 'No Retur', header_table)
		worksheet.write(row,1, 'Tgl Retur', header_table)
		worksheet.write(row,2, 'Deskripsi Barang', header_table)		
		worksheet.write(row,3, 'No SJ customer', header_table)
		worksheet.write(row,4, 'Nama Pembeli', header_table)
		worksheet.write(row,5, 'Kuantitas', header_table)
		worksheet.write(row,6, 'Jenis Retur', header_table)
		worksheet.write(row,7, 'Alasan Retur', header_table)
		
		
		row = 7
		for rec in data:		
			worksheet.write(row, 0, (rec.get('so_name')),body_table)
			worksheet.write(row, 1, rec.get('tgl_terima').strftime("%d %b %Y") ,body_table)
			worksheet.write(row, 2, (rec.get('deskripsi')),body_table)
			worksheet.write(row, 3, (rec.get('no_sj_customer') or rec.get('no_sj_wim')),body_table)
			worksheet.write(row, 4, (rec.get('partner_name')),body_table)		
			worksheet.write(row, 5, (rec.get('qty_terima') or '0'),body_right_table)
			worksheet.write(row, 6, (rec.get('tipe_retur')),body_table)
			worksheet.write(row, 7, (rec.get('alasan')),body_table)	
			
			


			row = row + 1
		
	
		workbook.close()
		out = base64.b64encode(fp.getvalue())
		fp.close()
		filename = ('Laporan Retur Penjualan %s_%s_sd_%s.xlsx') % (self.company_id.name,self.start_date,self.end_date )
		return self.set_data_excel(out, filename)

	def set_data_excel(self, out, filename):
		""" Update data_file and name based from previous process output. And return action url for download excel. """
		self.write({'data_file': out, 'name': filename})

		return {
			'type':
			'ir.actions.act_url',
			'name':
			filename,
			'url':
			'/web/content/%s/%s/data_file/%s' % (
				self._name,
				self.id,
				filename,
			),
		}

