# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
import logging
_logger = logging.getLogger(__name__)
import base64
from datetime import date
from io import BytesIO
from calendar import monthrange
from itertools import groupby

try:
	from odoo.tools.misc import xlsxwriter
except ImportError:
	import xlsxwriter

MONTH = [('1', 'January'), ('2', 'February'), ('3', 'March'),
			  ('4', 'April'), ('5', 'May'), ('6', 'June'), ('7', 'July'),
			  ('8', 'August'), ('9', 'September'), ('10', 'October'),
			  ('11', 'November'), ('12', 'December')]

class WizardPurchaseRawMaterialReport(models.TransientModel):
	_name = 'wizard.purchase.raw.material.report'
	_12cription = 'Wizard Raw Material Purchasing Report'

	YEARS = [(str(num), str(num))
			 for num in range(2019, (date.today().year) + 1)]

	month = fields.Selection(MONTH, string='Month')
	year = fields.Selection(YEARS, string='Year', required=True)
	type = fields.Selection([
		('monthly', 'By Month'),
		('yearly', 'By Year')
	], string='Type Report')
	company_id = fields.Many2one('res.company',
								 string='Company',
								 required=True, default=lambda self:self.env.company.id)
	name = fields.Char(string="Filename", readonly=True)
	data_file = fields.Binary(string="File", readonly=True)

	def button_print(self):
		if self.type == 'monthly':
			data = self._get_data_purchase()
			return self.generate_excel(data)
		else:
			data = self._get_data_purchase_yearly()
			return self.generate_excel_yearly(data)

	def _get_data_purchase(self):
		query = """
			SELECT 
				pt.default_code AS product_code, 
				pt.name As product_name,
				aml.move_name AS bill_name, 
				po.name AS po_name, 
				aml.date As bill_date,
				rp.code As partner_code, 
				rp.name AS partner_name, 
				aml.quantity AS qty_invoiced,
				uom.name AS uom_name,
				aml.amount_currency AS valas,
				rc.name AS valas_name,
				ABS(aml.balance) AS domestik,
				ABS(aml.balance) / aml.quantity AS biaya_rata2 
			FROM 
				purchase_order_line po_line
			JOIN
				purchase_order po ON po.id = po_line.order_id
			JOIN 
				res_partner rp ON rp.id = po_line.partner_id
			JOIN 
				product_product pp ON pp.id = po_line.product_id
			JOIN 
				product_template pt ON pt.id = pp.product_tmpl_id
			LEFT JOIN 
				account_move_line aml ON aml.purchase_line_id = po_line.id
			LEFT JOIN 
				uom_uom uom ON uom.id = aml.product_uom_id
			LEFT JOIN 
				res_currency rc ON rc.id = aml.currency_id
			WHERE aml.date BETWEEN %s AND %s
			ORDER BY pt.default_code,rp.code,aml.move_name ;
		"""
		start_date = date(int(self.year), int(self.month),1)
		last_day = monthrange(int(self.year),int(self.month))[1]
		end_date = date(int(self.year),int(self.month),last_day)
		self._cr.execute(query, (start_date,end_date))
		res = self._cr.dictfetchall()
		return res
		
	def _get_data_purchase_yearly(self):
		query = """
			SELECT
				COL.product_name, COL.partner_name,
				sum(case when COL.month=1 THEN COL.qty_invoiced ELSE 0 END) AS qty_1,
				sum(case when COL.month=1 THEN COL.domestik ELSE 0 END) AS total_1,
				sum(case when COL.month=1 THEN COL.biaya_rata2 ELSE 0 END) AS harga_1,
				sum(case when COL.month=2 THEN COL.qty_invoiced ELSE 0 END) AS qty_2,
				sum(case when COL.month=2 THEN COL.domestik ELSE 0 END) AS total_2,
				sum(case when COL.month=2 THEN COL.biaya_rata2 ELSE 0 END) AS harga_2,
				sum(case when COL.month=3 THEN COL.qty_invoiced ELSE 0 END) AS qty_3,
				sum(case when COL.month=3 THEN COL.domestik ELSE 0 END) AS total_3,
				sum(case when COL.month=3 THEN COL.biaya_rata2 ELSE 0 END) AS harga_3,
				sum(case when COL.month=4 THEN COL.qty_invoiced ELSE 0 END) AS qty_4,
				sum(case when COL.month=4 THEN COL.domestik ELSE 0 END) AS total_4,
				sum(case when COL.month=4 THEN COL.biaya_rata2 ELSE 0 END) AS harga_4,
				sum(case when COL.month=5 THEN COL.qty_invoiced ELSE 0 END) AS qty_5,
				sum(case when COL.month=5 THEN COL.domestik ELSE 0 END) AS total_5,
				sum(case when COL.month=5 THEN COL.biaya_rata2 ELSE 0 END) AS harga_5,
				sum(case when COL.month=6 THEN COL.qty_invoiced ELSE 0 END) AS qty_6,
				sum(case when COL.month=6 THEN COL.domestik ELSE 0 END) AS total_6,
				sum(case when COL.month=6 THEN COL.biaya_rata2 ELSE 0 END) AS harga_6,
				sum(case when COL.month=7 THEN COL.qty_invoiced ELSE 0 END) AS qty_7,
				sum(case when COL.month=7 THEN COL.domestik ELSE 0 END) AS total_7,
				sum(case when COL.month=7 THEN COL.biaya_rata2 ELSE 0 END) AS harga_7,
				sum(case when COL.month=8 THEN COL.qty_invoiced ELSE 0 END) AS qty_8,
				sum(case when COL.month=8 THEN COL.domestik ELSE 0 END) AS total_8,
				sum(case when COL.month=8 THEN COL.biaya_rata2 ELSE 0 END) AS harga_8,
				sum(case when COL.month=9 THEN COL.qty_invoiced ELSE 0 END) AS qty_9,
				sum(case when COL.month=9 THEN COL.domestik ELSE 0 END) AS total_9,
				sum(case when COL.month=9 THEN COL.biaya_rata2 ELSE 0 END) AS harga_9,
				sum(case when COL.month=10 THEN COL.qty_invoiced ELSE 0 END) AS qty_10,
				sum(case when COL.month=10 THEN COL.domestik ELSE 0 END) AS total_10,
				sum(case when COL.month=10 THEN COL.biaya_rata2 ELSE 0 END) AS harga_10,
				sum(case when COL.month=11 THEN COL.qty_invoiced ELSE 0 END) AS qty_11,
				sum(case when COL.month=11 THEN COL.domestik ELSE 0 END) AS total_11,
				sum(case when COL.month=11 THEN COL.biaya_rata2 ELSE 0 END) AS harga_11,
				sum(case when COL.month=12 THEN COL.qty_invoiced ELSE 0 END) AS qty_12,
				sum(case when COL.month=12 THEN COL.domestik ELSE 0 END) AS total_12,
				sum(case when COL.month=12 THEN COL.biaya_rata2 ELSE 0 END) AS harga_12
			FROM (
				SELECT 
					pt.name As product_name,
					rp.name AS partner_name,
					EXTRACT('MONTH' from aml.date) AS month,
					EXTRACT('YEAR' from aml.date) AS year,
					aml.quantity AS qty_invoiced,
					ABS(aml.balance) AS domestik,
					ABS(aml.balance) / aml.quantity AS biaya_rata2 
				FROM purchase_order_line po_line
				JOIN res_partner rp ON rp.id = po_line.partner_id
				JOIN product_product pp ON pp.id = po_line.product_id
				JOIN product_template pt ON pt.id = pp.product_tmpl_id
				LEFT JOIN account_move_line aml ON aml.purchase_line_id = po_line.id
				LEFT JOIN uom_uom uom ON uom.id = aml.product_uom_id
				LEFT JOIN res_currency rc ON rc.id = aml.currency_id
				ORDER BY pt.default_code,rp.code,aml.move_name
				) AS COL
			WHERE COL.year = %s
			GROUP BY  COL.product_name, COL.partner_name
			ORDER BY COL.product_name, COL.partner_name;
		"""
		self._cr.execute(query, (self.year,))
		res = self._cr.dictfetchall()
		return res

	def generate_excel(self,data):
		""" Generate excel based from purchase.order record. """
		fp = BytesIO()
		workbook = xlsxwriter.Workbook(fp)
		worksheet = workbook.add_worksheet()
		
		# ========== Format ==============
		header_top_table = workbook.add_format({'bold':True,'valign':'vcenter','align':'center','text_wrap':True})
		header_top_table.set_font_size(14)
		header_top_table.set_font_name('Times New Roman')

		header_table = workbook.add_format({'bold':True,'valign':'vcenter','align':'center','text_wrap':True})
		header_table.set_font_size(10)
		header_table.set_font_name('Times New Roman')
		
		header_product_table = workbook.add_format({'bold':True,'valign':'vcenter','align':'left','text_wrap':True})
		header_product_table.set_font_size(10)
		header_product_table.set_font_name('Times New Roman')
		header_product_table.set_bg_color('yellow')

		header_product_number_table = workbook.add_format({'bold':True,'valign':'vcenter','align':'right','text_wrap':True})
		header_product_number_table.set_font_size(10)
		header_product_number_table.set_font_name('Times New Roman')
		header_product_number_table.set_num_format('#,##0.00')

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

		worksheet.set_column('A:A', 15)
		worksheet.set_column('B:B', 25)
		worksheet.set_column('C:D', 15)
		worksheet.set_column('E:E', 25)
		worksheet.set_column('F:M', 10)

		# ========== Header ==============
		start_date = date(date.today().year,int(self.month),1)
		last_day = monthrange(int(date.today().year),int(self.month))[1]
		end_date = date(date.today().year,int(self.month),last_day)
		worksheet.merge_range('A2:Q2',self.company_id.name,header_top_table)
		worksheet.merge_range('A3:Q3','Pembelian Barang per Pemasok',header_top_table)
		worksheet.merge_range('A4:Q4',(_('Dari %s s/d %s') % (start_date.strftime("%d %b %Y"),end_date.strftime("%d %b %Y"))),header_table)

		worksheet.write('A6', 'No. Barang',header_table)
		worksheet.write('B6', 'Desk Barang',header_table)
		worksheet.write('B7', 'No. Faktur',header_table)
		worksheet.write('C7', 'No. PO',header_table)
		worksheet.write('D7', 'Tgl Faktur',header_table)
		worksheet.write('E7', 'No. Pemasok',header_table)
		worksheet.write('F7', 'Nama Pemasok',header_table)
		worksheet.write('G7', 'Kts',header_table)
		worksheet.write('H7', 'Satuan',header_table)
		worksheet.write('I7', 'Kts. Standard',header_table)
		worksheet.write('J7', 'Jml (Valas)',header_table)
		worksheet.write('K7', 'Mata Uang',header_table)
		worksheet.write('L7', 'Nilai Tukar',header_table)
		worksheet.write('M7', 'Jml (Domestik)',header_table)
		worksheet.write('N7', 'Biaya Rata2',header_table)
		
		row = 8
		for products, data_product in groupby(data, lambda product : [product.get('product_code'),product.get('product_name')]):
			worksheet.write(('A%s')%(row), products[0],header_product_table)
			worksheet.write(('B%s')%(row), products[1],header_product_table)
			row = row + 1
			sum_kts = []
			sum_valas = []
			sum_domestik = []
			sum_rata = []
			for partners , data_partner in groupby(list(data_product), lambda partner: [partner.get('partner_code'),partner.get('partner_name')]):
				sum_sub_kts = []
				sum_sub_valas = []
				sum_sub_domestik = []
				sum_sub_rata = []
				for rec in list(data_partner):
					if partners[0] == rec.get('partner_code'):
						worksheet.write(('B%s')%(row), ('%s') % (rec.get('bill_name') or '-'),body_table)
						worksheet.write(('C%s')%(row), ('%s') % (rec.get('po_name') or '-'),body_table)
						worksheet.write(('D%s')%(row), ('%s') % (rec.get('bill_date') or '-'),body_table)
						worksheet.write(('E%s')%(row), ('%s') % (rec.get('partner_code') or '-'),body_table)
						worksheet.write(('F%s')%(row), ('%s') % (rec.get('partner_name') or '-'),body_table)
						worksheet.write(('G%s')%(row), rec.get('qty_invoiced') or 0.0,body_right_table)
						worksheet.write(('H%s')%(row), ('%s') % (rec.get('uom_name') or '-'),body_table)
						worksheet.write(('I%s')%(row), rec.get('qty_invoiced') or 0.0,body_right_table)
						worksheet.write(('J%s')%(row), rec.get('valas') or 0.0,body_right_table)
						worksheet.write(('K%s')%(row), ('%s') % (rec.get('valas_name') or '-'),body_table)
						worksheet.write(('L%s')%(row), ('%s') % ( '-'),body_right_table)
						worksheet.write(('M%s')%(row), ('%s') % rec.get('domestik') or 0.0,body_right_table)
						worksheet.write(('N%s')%(row), ('%s') % rec.get('biaya_rata2') or 0.0,body_right_table)
						row = row + 1
						sum_sub_kts.append(rec.get('qty_invoiced'))
						sum_sub_valas.append(rec.get('valas'))
						sum_sub_domestik.append(rec.get('domestik'))
						sum_sub_rata.append(rec.get('biaya_rata2'))
				worksheet.write(('B%s')%(row), ('Total dari %s') % (partners[0] or partners[1]),header_table)
				worksheet.write(('I%s')%(row), ('%s') % (int(sum(sum_sub_kts))),header_product_number_table)
				worksheet.write(('J%s')%(row), ('%s') % (int(sum(sum_sub_valas))),header_product_number_table)
				worksheet.write(('M%s')%(row), ('%s') % (int(sum(sum_sub_domestik))),header_product_number_table)
				worksheet.write(('N%s')%(row), ('%s') % (int(sum(sum_sub_rata))),header_product_number_table)
				sum_kts.append(sum(sum_sub_kts))
				sum_valas.append(sum(sum_sub_valas))
				sum_domestik.append(sum(sum_sub_domestik))
				sum_rata.append(sum(sum_sub_rata))
				row = row + 1
			worksheet.write(('A%s')%(row), ('Total dari %s') % (products[0] or products[1]),header_table)
			worksheet.write(('I%s')%(row), ('%s') % (int(sum(sum_kts))),header_product_number_table)
			worksheet.write(('J%s')%(row), ('%s') % (int(sum(sum_valas))),header_product_number_table)
			worksheet.write(('M%s')%(row), ('%s') % (int(sum(sum_domestik))),header_product_number_table)
			worksheet.write(('N%s')%(row), ('%s') % (int(sum(sum_rata))),header_product_number_table)
			row = row + 1

		workbook.close()
		out = base64.b64encode(fp.getvalue())
		fp.close()
		filename = ('purchase_raw_material_%s_%s_sd_%s.xlsx') % (self.company_id.name,start_date,end_date )
		return self.set_data_excel(out, filename)

	def generate_excel_yearly(self,data):
		""" Generate excel based from purchase.order record. """
		fp = BytesIO()
		workbook = xlsxwriter.Workbook(fp)
		worksheet = workbook.add_worksheet()
		
		# ========== Format ==============
		header_top_table = workbook.add_format({'bold':True,'valign':'vcenter','align':'center','text_wrap':True})
		header_top_table.set_font_size(14)
		header_top_table.set_font_name('Times New Roman')
		header_top_table.set_border()
		header_top_table.set_fg_color('#fbd4b4')

		header_table = workbook.add_format({'bold':True,'valign':'vcenter','align':'left','text_wrap':True})
		header_table.set_font_size(10)
		header_table.set_font_name('Times New Roman')
		header_table.set_border()

		body_table = workbook.add_format()
		body_table.set_align('left')
		body_table.set_align('vcenter')
		body_table.set_font_size(10)
		body_table.set_font_name('Times New Roman')
		body_table.set_border()

		body_right_table = workbook.add_format()
		body_right_table.set_align('right')
		body_right_table.set_align('vcenter')
		body_right_table.set_font_size(10)
		body_right_table.set_font_name('Times New Roman')
		body_right_table.set_num_format('#,##0.00')
		body_right_table.set_border()

		worksheet.set_column('A:B', 25)
		worksheet.set_column('B:B', 35)
		worksheet.set_column('C:AL', 10)

		# ========== Header ==============
		worksheet.merge_range('A2:A3', 'Nama Material',header_top_table)
		worksheet.merge_range('B2:B3', 'Nama Supplier',header_top_table)
		
		row = 3
		is_header = True
		nama_barang = ''
		for rec in data:
			if nama_barang != rec.get('product_name'):
				row = row + 1
				worksheet.write(row, 0, ('%s') % (rec.get('product_name') or '-'),header_table)
				nama_barang = rec.get('product_name')
			else:
				worksheet.write(row, 0, '',header_table)

			worksheet.write(row, 1, ('%s') % (rec.get('partner_name') or '-'),header_table)

			first_col = 2
			for month in MONTH:
				if is_header:
					worksheet.merge_range(1, first_col, 1, first_col+2, ('%s')%(month[1]) , header_top_table)
					worksheet.write(2, first_col,'Qty',header_top_table)
					worksheet.write(2, first_col + 1,'Total',header_top_table)
					worksheet.write(2, first_col + 2,'Harga',header_top_table)
				qty = ('qty_%s') % (str(month[0]))
				total = ('total_%s') % (str(month[0]))
				harga = ('harga_%s') % (str(month[0]))
				worksheet.write(row, first_col, rec.get(qty) or 0.0, body_right_table)
				worksheet.write(row, first_col + 1, rec.get(total) or 0.0, body_right_table)
				worksheet.write(row, first_col + 2, rec.get(harga) or 0.0, body_right_table)

				first_col = first_col + 3
			row = row + 1
			is_header = False

		workbook.close()
		out = base64.b64encode(fp.getvalue())
		fp.close()
		filename = ('purchase_raw_material_resume_%s_%s.xlsx') % (self.company_id.name,self.year )
		return self.set_data_excel(out, filename)

	def set_data_excel(self, out, filename):
		""" Update data_file and name based from previous process output. And return action url for download excel. """
		self.write({'data_file': out, 'name': filename})

		return {
			'type':
			'ir.actions.act_url',
			'name':
			filename,
			# 'url':
			# '/web/content/%s/%s/data_file/%s' % (
			# 	self._name,
			# 	self.id,
			# 	filename,
			# ),
			'url':'/web/content?model=wizard.purchase.raw.material.report&field=data_file&filename_field=name&id=%s&download=true&filename=%s' %(self.id, filename,),
		}

