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

class WizardRiwayatPurchaseOrderReport(models.TransientModel):
	_name = 'wizard.riwayat.purchase.order.report'
	_description = 'Wizard Riwayat Purchase Order Report'

	start_date = fields.Date(string='Start Date', required=True)
	end_date = fields.Date(string='End Date', required=True)
	company_id = fields.Many2one('res.company',
								 string='Company',
								 required=True)
	name = fields.Char(string="Filename", readonly=True)
	data_file = fields.Binary(string="File", readonly=True)
	vendor_ids = fields.Many2many('res.partner', string="Vendor", domain=[('supplier','=',True)])
	product_ids = fields.Many2many('product.product',string='Products')
	group_by = fields.Selection([('product','Product'),('vendor','Vendor')],string='Group By', default='product')
	
	def button_print(self):
		data = self._get_data_purchase()
		if not data :
			raise ValidationError(_("Data Tidak ditemukan, Silahkan coba dengan Filter lainnya"))
		return self.generate_excel(data)

	def _get_data_purchase(self):
		vendor_filter = ""
		
		if self.vendor_ids:
			if len(self.vendor_ids) == 1:
				data_tuple = "(%s)" % self.vendor_ids.id
			else:
				data_tuple = tuple(self.vendor_ids.ids)
			vendor_filter = ("AND po.partner_id IN %s") % (str(data_tuple))
		product_filter = ""
		if self.product_ids:
			if len(self.product_ids) == 1:
				product_tuple = "(%s)" % self.product_ids.id
			else:
				product_tuple = tuple(self.product_ids.ids)
			product_filter = (" AND po_line.product_id IN %s") % (str(product_tuple))
		query = """
			SELECT 
				rp.name AS partner_name, 
				po.name AS po_name, 
				po.date_order AS date_order, 
				pt.name AS product_name, 
				po_line.product_qty AS kts,
				po_line.price_unit AS price_unit, 
				po_line.qty_received AS total_kts,
				(po_line.product_qty - po_line.qty_received) AS saldo_kts,
				CASE WHEN po.status_po = 'open' THEN 'Sedang Proses' 
				WHEN po.status_po = 'done' AND po_line.product_qty != po_line.qty_received THEN 'PO Ditutup'
				WHEN po.status_po = 'done' AND po_line.product_qty = po_line.qty_received THEN 'Terima Penuh'
				WHEN po.status_po = 'close' THEN 'PO ditutup' ELSE 'No Status' END AS status,
				sp.no_sj_vendor as no_sj_vendor,
				po_line.name as deskripsi,
				sp.no_sj_wim as no_sj_wim,
				sp.date_received as tgl_terima,
				CASE WHEN sp.origin LIKE %s THEN -1 * sm.product_uom_qty ELSE sm.product_uom_qty END as qty_terima
			FROM purchase_order po
			LEFT JOIN purchase_order_line po_line ON po_line.order_id = po.id
			LEFT JOIN res_partner rp ON rp.id = po.partner_id
			LEFT JOIN product_product pp ON pp.id = po_line.product_id
			LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
			LEFT JOIN stock_move sm ON sm.purchase_line_id = po_line.id
			LEFT JOIN stock_picking sp ON sm.picking_id = sp.id
			WHERE sp.state = 'done' AND po.company_id = %s AND po.date_order BETWEEN %s AND %s """ + vendor_filter + product_filter + """
			ORDER BY pt.name, po.id, rp.name, sp.date_received;
		"""
		self._cr.execute(query, ('Return %', self.company_id.id,self.start_date,self.end_date))
		res = self._cr.dictfetchall()
		return res

	def generate_excel(self,data):
		""" Generate excel based from purchase.order record. """
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
		worksheet.merge_range('A2:L2',self.company_id.name,header_table)
		worksheet.merge_range('A3:L3','Riwayat Pesanan Pembelian',header_table)
		worksheet.merge_range('A4:L4',(_('Dari %s s/d %s') % (self.start_date.strftime("%d %b %Y"),self.end_date.strftime("%d %b %Y"))),header_table)

		# worksheet.merge_range('B6:G6', 'No. Pesanan',header_table)
		# worksheet.write('C7', 'Tgl Pesan',header_table)
		# worksheet.merge_range('E7:G7', 'Deskripsi Barang',header_table)
		# worksheet.write('I7', 'Qty. Pesan',header_table)
		# worksheet.write('K7', 'Harga Satuan',header_table)
		# worksheet.write('M7', 'Total Qty. Diterima',header_table)
		# worksheet.write('O7', 'Saldo Qty.',header_table)
		# worksheet.merge_range('Q7:R7', 'Status Pesanan',header_table)
		row = 6
		worksheet.write(row,0, 'Nama Barang', header_table)
		worksheet.write(row,1, 'No. PO', header_table)	
		worksheet.write(row,2, 'Nama Vendor', header_table)		
		worksheet.write(row,3, 'Tgl. Pesan', header_table)
		worksheet.write(row,4, 'Deskripsi Barang', header_table)
		worksheet.write(row,5, 'Qty Pesan', header_table)
		worksheet.write(row,6, 'No. SJ Vendor', header_table)
		worksheet.write(row,7, 'Tgl. Terima', header_table)
		worksheet.write(row,8, 'Qty Diterima', header_table)
		worksheet.write(row,9, 'Total Qty Terima', header_table)
		worksheet.write(row,10, 'Saldo Qty', header_table)
		worksheet.write(row,11, 'Status Barang', header_table)
		
		row = 7
		nama_pemasok = ''
		nama_po = ''
		nama_po_barang = ''
		nama_barang = ''
		deskripsi = ''
		tgl_pesan = ''
		qty_pesan = ''
		total_all = 0.0
		nama_barang_old = ''
		for rec in data:
			# if nama_pemasok != rec.get('partner_name'):
			# 	worksheet.write(row, 0, (rec.get('partner_name') or '-'),body_table)
			# 	nama_pemasok = rec.get('partner_name')
			# 	# row = row + 1
			
			if nama_barang != rec.get('product_name'):
				
					# row = row + 1			
				if len(nama_barang) > 1:
					worksheet.write(row+2, 0, (rec.get('product_name') or '-'),body_table)
				else:					
					worksheet.write(row, 0, (rec.get('product_name') or '-'),body_table)
				nama_barang = rec.get('product_name')
					

			if nama_po != rec.get('po_name'):
				if len(nama_po) > 1:
					worksheet.merge_range(('C%s:H%s')%(row+1,row+1), ('%s') % ('Total dari '+ nama_barang_old),header_table)
					worksheet.write(row, 8, total_all ,header_right_table)
					total_all = 0.0
					row = row + 2
				worksheet.write(row, 1, (rec.get('po_name') or '-'),body_table)
				worksheet.write(row, 2, (rec.get('partner_name') or '-'),body_table)
				worksheet.write(row, 3, (rec.get('date_order').strftime("%d %b %Y") or '-'),body_table)
				worksheet.write(row, 4, (rec.get('deskripsi') or '-'),body_table)
				worksheet.write(row, 5, (rec.get('kts') or '0'),body_right_table)
				worksheet.write(row, 9, (rec.get('total_kts') or '0'),body_right_table)
				worksheet.write(row, 10, (rec.get('saldo_kts') or '0'),body_right_table)
				worksheet.write(row, 11, (rec.get('status') or '-'),body_table)
				nama_po = rec.get('po_name')
				nama_barang_old = rec.get('product_name')
				# row = row + 1
			

			worksheet.write(row, 6, (rec.get('no_sj_vendor') or rec.get('no_sj_wim')),body_table)
			worksheet.write(row, 7, rec.get('tgl_terima').strftime("%d %b %Y") ,body_table)
			worksheet.write(row, 8, (rec.get('qty_terima') or '0'),body_right_table)
			total_all += rec.get('qty_terima')


			# worksheet.write(('C%s')%(row), rec.get('date_order').strftime("%d %b %Y"),body_right_table)
			# worksheet.merge_range(('E%s:G%s')%(row,row), ('%s') % (rec.get('product_name') or '-'),body_table)
			# worksheet.write(('H%s')%(row), rec.get('no_sj_vendor'),body_right_table)
			# worksheet.write(('I%s')%(row), rec.get('kts'),body_right_table)
			# worksheet.write(('K%s')%(row), rec.get('price_unit'),body_right_table)
			# worksheet.write(('M%s')%(row), rec.get('total_kts'),body_right_table)
			# worksheet.write(('O%s')%(row), rec.get('saldo_kts'),body_right_table)
			# worksheet.merge_range(('Q%s:R%s')%(row,row), ('%s') % (rec.get('status') or '-'),body_table)
			row = row + 1
		
		worksheet.merge_range(('C%s:H%s')%(row+1,row+1), ('%s') % ('Total dari '+ nama_barang),header_table)
		worksheet.write(row, 8, total_all ,header_right_table)
		workbook.close()
		out = base64.b64encode(fp.getvalue())
		fp.close()
		filename = ('Riwayat Pemberlian %s_%s_sd_%s.xlsx') % (self.company_id.name,self.start_date,self.end_date )
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

