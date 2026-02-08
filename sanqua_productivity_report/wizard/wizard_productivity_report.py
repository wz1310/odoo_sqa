# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
import logging
_logger = logging.getLogger(__name__)
import base64
from datetime import date, datetime
from io import BytesIO
from calendar import monthrange

try:
	from odoo.tools.misc import xlsxwriter
except ImportError:
	import xlsxwriter

class WizardProductivityReport(models.TransientModel):
	_name = 'wizard.productivity.report'
	_description = 'Wizard Productivity Report'

	YEARS = [(str(num), str(num)) for num in range(2020, (datetime.now().year)+10 )]
 
	year = fields.Selection(YEARS, string='Periode',required=True)
	mesin_ids = fields.Many2many('mrp.mesin', string='Mesin')
	product_ids = fields.Many2many('product.product', string='Product')
	type_of_result = fields.Selection([
		('mesin', 'By Mesin'),
		('product', 'By Brand')
	], string='Type Of Result')
	company_id = fields.Many2one('res.company',
								 string='Company',
								 required=True, default=lambda self: self.env.company)
	name = fields.Char(string="Filename", readonly=True)
	data_file = fields.Binary(string="File", readonly=True)

	def button_print(self):
		if self.type_of_result == 'mesin':
			data = self._get_data_result_by_mesin()
			return self.generate_excel_result_by_mesin(data)
		else:
			data = self._get_data_result_by_product()
			return self.generate_excel_result_by_product(data)

	def _get_data_result_by_mesin(self):
		query = """
			SELECT 
				mm.name AS name,
				sum(sm.product_uom_qty) FILTER (WHERE to_char(sm.date,'YYYY') = %s AND to_char(sm.date,'MM') = '01') AS januari,
				sum(sm.product_uom_qty) FILTER (WHERE to_char(sm.date,'YYYY') = %s AND to_char(sm.date,'MM') = '02')AS februari,
				sum(sm.product_uom_qty) FILTER (WHERE to_char(sm.date,'YYYY') = %s AND to_char(sm.date,'MM') = '03')AS maret,
				sum(sm.product_uom_qty) FILTER (WHERE to_char(sm.date,'YYYY') = %s AND to_char(sm.date,'MM') = '04')AS april,
				sum(sm.product_uom_qty) FILTER (WHERE to_char(sm.date,'YYYY') = %s AND to_char(sm.date,'MM') = '05')AS mei,
				sum(sm.product_uom_qty) FILTER (WHERE to_char(sm.date,'YYYY') = %s AND to_char(sm.date,'MM') = '06')AS juni,
				sum(sm.product_uom_qty) FILTER (WHERE to_char(sm.date,'YYYY') = %s AND to_char(sm.date,'MM') = '07')AS juli,
				sum(sm.product_uom_qty) FILTER (WHERE to_char(sm.date,'YYYY') = %s AND to_char(sm.date,'MM') = '08')AS agustus,
				sum(sm.product_uom_qty) FILTER (WHERE to_char(sm.date,'YYYY') = %s AND to_char(sm.date,'MM') = '09')AS september,
				sum(sm.product_uom_qty) FILTER (WHERE to_char(sm.date,'YYYY') = %s AND to_char(sm.date,'MM') = '10')AS oktober,
				sum(sm.product_uom_qty) FILTER (WHERE to_char(sm.date,'YYYY') = %s AND to_char(sm.date,'MM') = '11')AS november,
				sum(sm.product_uom_qty) FILTER (WHERE to_char(sm.date,'YYYY') = %s AND to_char(sm.date,'MM') = '12')AS desember
			FROM mrp_production mp
			JOIN mrp_mesin mm ON mp.mesin_id = mm.id
			JOIN stock_move sm ON sm.production_id = mp.id
			WHERE mp.state  = 'done' AND sm.state = 'done' AND mp.company_id = %s
			GROUP BY sm.date,mm.name,mp.company_id
			ORDER BY sm.date,mm.name,mp.company_id;

		"""
		param = []
		for rec in range(0,12):
			param.append(self.year)
		param.append(self.company_id.id)
		self._cr.execute(query, param)
		res = self._cr.dictfetchall()
		return res

	def _get_data_result_by_product(self):
		query = """
			SELECT 
				pt.name AS name,
				sum(sm.product_uom_qty) FILTER (WHERE to_char(sm.date,'YYYY') = %s AND to_char(sm.date,'MM') = '01') AS januari,
				sum(sm.product_uom_qty) FILTER (WHERE to_char(sm.date,'YYYY') = %s AND to_char(sm.date,'MM') = '02')AS februari,
				sum(sm.product_uom_qty) FILTER (WHERE to_char(sm.date,'YYYY') = %s AND to_char(sm.date,'MM') = '03')AS maret,
				sum(sm.product_uom_qty) FILTER (WHERE to_char(sm.date,'YYYY') = %s AND to_char(sm.date,'MM') = '04')AS april,
				sum(sm.product_uom_qty) FILTER (WHERE to_char(sm.date,'YYYY') = %s AND to_char(sm.date,'MM') = '05')AS mei,
				sum(sm.product_uom_qty) FILTER (WHERE to_char(sm.date,'YYYY') = %s AND to_char(sm.date,'MM') = '06')AS juni,
				sum(sm.product_uom_qty) FILTER (WHERE to_char(sm.date,'YYYY') = %s AND to_char(sm.date,'MM') = '07')AS juli,
				sum(sm.product_uom_qty) FILTER (WHERE to_char(sm.date,'YYYY') = %s AND to_char(sm.date,'MM') = '08')AS agustus,
				sum(sm.product_uom_qty) FILTER (WHERE to_char(sm.date,'YYYY') = %s AND to_char(sm.date,'MM') = '09')AS september,
				sum(sm.product_uom_qty) FILTER (WHERE to_char(sm.date,'YYYY') = %s AND to_char(sm.date,'MM') = '10')AS oktober,
				sum(sm.product_uom_qty) FILTER (WHERE to_char(sm.date,'YYYY') = %s AND to_char(sm.date,'MM') = '11')AS november,
				sum(sm.product_uom_qty) FILTER (WHERE to_char(sm.date,'YYYY') = %s AND to_char(sm.date,'MM') = '12')AS desember
			FROM mrp_production mp
			JOIN product_product pp ON mp.product_id = pp.id
			JOIN product_template pt ON pp.product_tmpl_id = pt.id
			JOIN stock_move sm ON sm.production_id = mp.id
			WHERE mp.state  = 'done' AND sm.state = 'done' AND mp.company_id = %s
			GROUP BY mp.product_id,pt.name,mp.company_id
			ORDER BY mp.product_id,pt.name,mp.company_id;
		"""
		param = []
		for rec in range(0,12):
			param.append(self.year)
		param.append(self.company_id.id)
		self._cr.execute(query, param)
		res = self._cr.dictfetchall()
		return res

	def generate_excel_result_by_mesin(self,data):
		""" Generate excel based from mrp.product group by mesin record. """
		fp = BytesIO()
		workbook = xlsxwriter.Workbook(fp)
		worksheet = workbook.add_worksheet()
		
		# ========== Format ==============
		header_table = workbook.add_format({'bold':True,'valign':'vcenter','align':'center','text_wrap':True})
		header_table.set_font_size(12)
		header_table.set_font_name('Times New Roman')

		header_mesin_table = workbook.add_format({'bold':True,'valign':'vcenter','align':'center','text_wrap':True})
		header_mesin_table.set_font_size(10)
		header_mesin_table.set_font_name('Times New Roman')
		header_mesin_table.set_border()
		header_mesin_table.set_num_format('#,##0.00')

		body_table = workbook.add_format()
		body_table.set_align('center')
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
		worksheet.set_column('B:B',20)
		worksheet.set_column('C:D',20)

		# ========== Header ==============
		worksheet.merge_range('B2:D2','Hasil Produksi / Mesin',header_table)
		worksheet.merge_range('B3:D3','Company ' + self.company_id.name,header_table)
		worksheet.merge_range('B4:D4','Tahun ' + str(self.year),header_table)

		worksheet.write('B6', 'SKU',header_mesin_table)
		worksheet.write('C6', 'Januari',header_mesin_table)
		worksheet.write('D6', 'Febuari',header_mesin_table)
		worksheet.write('E6', 'Maret',header_mesin_table)
		worksheet.write('F6', 'April',header_mesin_table)
		worksheet.write('G6', 'Mei',header_mesin_table)
		worksheet.write('H6', 'Juni',header_mesin_table)
		worksheet.write('I6', 'Juli',header_mesin_table)
		worksheet.write('J6', 'Agustus',header_mesin_table)
		worksheet.write('K6', 'September',header_mesin_table)
		worksheet.write('L6', 'Oktober',header_mesin_table)
		worksheet.write('M6', 'November',header_mesin_table)
		worksheet.write('N6', 'Desember',header_mesin_table)
		worksheet.write('O6', 'Total',header_mesin_table)
		
		row = 7
		total_produksi = []
		total_januari = 0.0
		total_febuari = 0.0
		total_maret = 0.0
		total_april = 0.0
		total_mei = 0.0
		total_juni = 0.0
		total_juli = 0.0
		total_agustus = 0.0
		total_september = 0.0
		total_oktober = 0.0
		total_november = 0.0
		total_desember = 0.0
		total_subtotal = 0.0
		for rec in data:
			subtotal = 0.0
			worksheet.write(('B%s')%(row), ('%s') % (rec.get('name') or '-'),body_table)
			worksheet.write(('C%s')%(row), ('%s') % (rec.get('januari') or '-'),body_table)
			worksheet.write(('D%s')%(row), ('%s') % (rec.get('febuari') or '-'),body_table)
			worksheet.write(('E%s')%(row), ('%s') % (rec.get('maret') or '-'),body_table)
			worksheet.write(('F%s')%(row), ('%s') % (rec.get('april') or '-'),body_table)
			worksheet.write(('G%s')%(row), ('%s') % (rec.get('mei') or '-'),body_table)
			worksheet.write(('H%s')%(row), ('%s') % (rec.get('juni') or '-'),body_table)
			worksheet.write(('I%s')%(row), ('%s') % (rec.get('juli') or '-'),body_table)
			worksheet.write(('J%s')%(row), ('%s') % (rec.get('agustus') or '-'),body_table)
			worksheet.write(('K%s')%(row), ('%s') % (rec.get('september') or '-'),body_table)
			worksheet.write(('L%s')%(row), ('%s') % (rec.get('oktober') or '-'),body_table)
			worksheet.write(('M%s')%(row), ('%s') % (rec.get('november') or '-'),body_table)
			worksheet.write(('N%s')%(row), ('%s') % (rec.get('desember') or '-'),body_table)
			subtotal = (rec.get('januari') or 0.0) + (rec.get('febuari') or 0.0) + (rec.get('maret') or 0.0) + (rec.get('april') or 0.0) +\
			(rec.get('mei') or 0.0) + (rec.get('juni') or 0.0) + (rec.get('juli') or 0.0) + (rec.get('agustus') or 0.0) + (rec.get('september') or 0.0) +\
			(rec.get('oktober') or 0.0) + (rec.get('november') or 0.0) + (rec.get('desember') or 0.0)
			worksheet.write(('O%s')%(row), subtotal,body_right_table)
			total_januari += (rec.get('januari') or 0.0)
			total_febuari += (rec.get('febuari') or 0.0)
			total_maret += (rec.get('maret') or 0.0)
			total_april += (rec.get('april') or 0.0)
			total_mei += (rec.get('mei') or 0.0)
			total_juni += (rec.get('juni') or 0.0)
			total_juli += (rec.get('juli') or 0.0)
			total_agustus += (rec.get('agustus') or 0.0)
			total_september += (rec.get('september') or 0.0)
			total_oktober += (rec.get('oktober') or 0.0)
			total_november += (rec.get('november') or 0.0)
			total_desember += (rec.get('desember') or 0.0)
			total_subtotal += subtotal
			row = row + 1
		worksheet.write(('B%s')%(row), 'Total',header_mesin_table)
		worksheet.write(('C%s')%(row), total_januari,header_mesin_table)
		worksheet.write(('D%s')%(row), total_febuari,header_mesin_table)
		worksheet.write(('E%s')%(row), total_maret,header_mesin_table)
		worksheet.write(('F%s')%(row), total_april,header_mesin_table)
		worksheet.write(('G%s')%(row), total_mei,header_mesin_table)
		worksheet.write(('H%s')%(row), total_juni,header_mesin_table)
		worksheet.write(('I%s')%(row), total_juli,header_mesin_table)
		worksheet.write(('J%s')%(row), total_agustus,header_mesin_table)
		worksheet.write(('K%s')%(row), total_september,header_mesin_table)
		worksheet.write(('L%s')%(row), total_oktober,header_mesin_table)
		worksheet.write(('M%s')%(row), total_november,header_mesin_table)
		worksheet.write(('N%s')%(row), total_desember,header_mesin_table)
		worksheet.write(('O%s')%(row), total_subtotal,header_mesin_table)

		workbook.close()
		out = base64.b64encode(fp.getvalue())
		fp.close()
		filename = ('hasil_produksi_per_mesin_%s_%s.xlsx') % (self.company_id.name,self.year)
		return self.set_data_excel(out, filename)

	def generate_excel_result_by_product(self,data):
		""" Generate excel based from mrp.product group by mesin record. """
		fp = BytesIO()
		workbook = xlsxwriter.Workbook(fp)
		worksheet = workbook.add_worksheet()
		
		# ========== Format ==============
		header_table = workbook.add_format({'bold':True,'valign':'vcenter','align':'center','text_wrap':True})
		header_table.set_font_size(12)
		header_table.set_font_name('Times New Roman')

		header_mesin_table = workbook.add_format({'bold':True,'valign':'vcenter','align':'center','text_wrap':True})
		header_mesin_table.set_font_size(10)
		header_mesin_table.set_font_name('Times New Roman')
		header_mesin_table.set_border()
		header_mesin_table.set_num_format('#,##0.00')

		body_table = workbook.add_format()
		body_table.set_align('center')
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
		worksheet.set_column('B:B',20)
		worksheet.set_column('C:D',20)

		# ========== Header ==============
		worksheet.merge_range('B2:D2','Hasil Produksi / SKU',header_table)
		worksheet.merge_range('B3:D3','Company ' + self.company_id.name,header_table)
		worksheet.merge_range('B4:D4','Tahun ' + str(self.year),header_table)

		worksheet.write('B6', 'SKU',header_mesin_table)
		worksheet.write('C6', 'Januari',header_mesin_table)
		worksheet.write('D6', 'Febuari',header_mesin_table)
		worksheet.write('E6', 'Maret',header_mesin_table)
		worksheet.write('F6', 'April',header_mesin_table)
		worksheet.write('G6', 'Mei',header_mesin_table)
		worksheet.write('H6', 'Juni',header_mesin_table)
		worksheet.write('I6', 'Juli',header_mesin_table)
		worksheet.write('J6', 'Agustus',header_mesin_table)
		worksheet.write('K6', 'September',header_mesin_table)
		worksheet.write('L6', 'Oktober',header_mesin_table)
		worksheet.write('M6', 'November',header_mesin_table)
		worksheet.write('N6', 'Desember',header_mesin_table)
		worksheet.write('O6', 'Total',header_mesin_table)
		
		row = 7
		total_produksi = []
		total_januari = 0.0
		total_febuari = 0.0
		total_maret = 0.0
		total_april = 0.0
		total_mei = 0.0
		total_juni = 0.0
		total_juli = 0.0
		total_agustus = 0.0
		total_september = 0.0
		total_oktober = 0.0
		total_november = 0.0
		total_desember = 0.0
		total_subtotal = 0.0
		for rec in data:
			subtotal = 0.0
			worksheet.write(('B%s')%(row), ('%s') % (rec.get('name') or '-'),body_table)
			worksheet.write(('C%s')%(row), ('%s') % (rec.get('januari') or '-'),body_table)
			worksheet.write(('D%s')%(row), ('%s') % (rec.get('febuari') or '-'),body_table)
			worksheet.write(('E%s')%(row), ('%s') % (rec.get('maret') or '-'),body_table)
			worksheet.write(('F%s')%(row), ('%s') % (rec.get('april') or '-'),body_table)
			worksheet.write(('G%s')%(row), ('%s') % (rec.get('mei') or '-'),body_table)
			worksheet.write(('H%s')%(row), ('%s') % (rec.get('juni') or '-'),body_table)
			worksheet.write(('I%s')%(row), ('%s') % (rec.get('juli') or '-'),body_table)
			worksheet.write(('J%s')%(row), ('%s') % (rec.get('agustus') or '-'),body_table)
			worksheet.write(('K%s')%(row), ('%s') % (rec.get('september') or '-'),body_table)
			worksheet.write(('L%s')%(row), ('%s') % (rec.get('oktober') or '-'),body_table)
			worksheet.write(('M%s')%(row), ('%s') % (rec.get('november') or '-'),body_table)
			worksheet.write(('N%s')%(row), ('%s') % (rec.get('desember') or '-'),body_table)
			subtotal = (rec.get('januari') or 0.0) + (rec.get('febuari') or 0.0) + (rec.get('maret') or 0.0) + (rec.get('april') or 0.0) +\
			(rec.get('mei') or 0.0) + (rec.get('juni') or 0.0) + (rec.get('juli') or 0.0) + (rec.get('agustus') or 0.0) + (rec.get('september') or 0.0) +\
			(rec.get('oktober') or 0.0) + (rec.get('november') or 0.0) + (rec.get('desember') or 0.0)
			worksheet.write(('O%s')%(row), subtotal,body_right_table)
			total_januari += (rec.get('januari') or 0.0)
			total_febuari += (rec.get('febuari') or 0.0)
			total_maret += (rec.get('maret') or 0.0)
			total_april += (rec.get('april') or 0.0)
			total_mei += (rec.get('mei') or 0.0)
			total_juni += (rec.get('juni') or 0.0)
			total_juli += (rec.get('juli') or 0.0)
			total_agustus += (rec.get('agustus') or 0.0)
			total_september += (rec.get('september') or 0.0)
			total_oktober += (rec.get('oktober') or 0.0)
			total_november += (rec.get('november') or 0.0)
			total_desember += (rec.get('desember') or 0.0)
			total_subtotal += subtotal
			row = row + 1
		worksheet.write(('B%s')%(row), 'Total',header_mesin_table)
		worksheet.write(('C%s')%(row), total_januari,header_mesin_table)
		worksheet.write(('D%s')%(row), total_febuari,header_mesin_table)
		worksheet.write(('E%s')%(row), total_maret,header_mesin_table)
		worksheet.write(('F%s')%(row), total_april,header_mesin_table)
		worksheet.write(('G%s')%(row), total_mei,header_mesin_table)
		worksheet.write(('H%s')%(row), total_juni,header_mesin_table)
		worksheet.write(('I%s')%(row), total_juli,header_mesin_table)
		worksheet.write(('J%s')%(row), total_agustus,header_mesin_table)
		worksheet.write(('K%s')%(row), total_september,header_mesin_table)
		worksheet.write(('L%s')%(row), total_oktober,header_mesin_table)
		worksheet.write(('M%s')%(row), total_november,header_mesin_table)
		worksheet.write(('N%s')%(row), total_desember,header_mesin_table)
		worksheet.write(('O%s')%(row), total_subtotal,header_mesin_table)

		workbook.close()
		out = base64.b64encode(fp.getvalue())
		fp.close()
		filename = ('hasil_produksi_per_sku_%s_%s.xlsx') % (self.company_id.name,self.year)
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

