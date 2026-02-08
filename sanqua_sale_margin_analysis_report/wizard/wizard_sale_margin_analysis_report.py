# -*- coding: utf-8 -*-
import logging
from odoo import _, api, fields, models
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

class WizardSaleMarginAnalysisReport(models.TransientModel):
	_name = 'wizard.sale.margin.analysis.report'
	_description = 'Wizard Sale Margin Analysis Report'

	YEARS = [(str(num), str(num))
			 for num in range(2019, (date.today().year) + 1)]

	user_id = fields.Many2one('res.users', string='Salesperson',required=True)
	team_ids = fields.Many2many('crm.team', string='Divisions')
	month = fields.Selection(MONTH, string='Month',required=True)
	year = fields.Selection(YEARS, string='Year', required=True)
	hpp_percent_factor1 = fields.Float(string='Percent Factor 1 (%)', default=65)
	hpp_percent_factor2 = fields.Float(string='Percent Factor 1 (%)', default=35)
	hpp_amount_factor1 = fields.Float(string='Amount Factor 1 (%)', default=9000)
	hpp_amount_factor2 = fields.Float(string='Amount Factor 1 (%)', default=8000)
	company_id = fields.Many2one('res.company',
								 string='Company',
								 required=True, default=lambda self:self.env.company.id)
	name = fields.Char(string="Filename", readonly=True)
	data_file = fields.Binary(string="File", readonly=True)

	@api.onchange('user_id','team_ids')
	def _onchange_user_id(self):
		if self.user_id:
			return {'domain':{'team_ids':[('id','in',self.user_id.sale_team_ids.ids)]}}
		else:
			return {'domain':{'team_ids':[('id','=',False)]}}


	def button_print(self):
		data = self._get_data()
		return self.generate_excel(data)

	def _get_data(self):
		query = """
			SELECT
				pt.name
				, sum(sut_line.qty) AS target_qty
				, sum(sr.qty_delivered) AS realisasi_qty
				, (sum(sr.qty_delivered) / sum(sut_line.qty)) * 100 AS achivement
				, sum(sr.price_subtotal) AS price_subtotal
				, sum(sr_ambil.discount_fixed_line) AS potongan_ambil
				, sum(so_line_promosi.price_subtotal) AS potongan_promosi
				, sum(so_line_dt.discount_fixed_line) AS potongan_dt
				, COALESCE(sum(sr.price_subtotal),0) - COALESCE(sum(sr_ambil.discount_fixed_line),0) - COALESCE(sum(so_line_promosi.price_subtotal),0) - COALESCE(sum(so_line_dt.discount_fixed_line),0) AS omset_nett
			FROM (SELECT 
					product_id, 
					user_id,
					team_id,
					EXTRACT(MONTH from date) AS month,
					EXTRACT(YEAR from date) AS year,
					company_id,
					sr.pricelist_id,
					sum(qty_delivered) as qty_delivered,
					sum(price_subtotal) as price_subtotal 
				FROM sale_report sr
				WHERE state = 'done'
				GROUP BY product_id, user_id,sr.pricelist_id,company_id,
					EXTRACT(MONTH from date),
					EXTRACT(YEAR from date),team_id
				ORDER BY product_id, user_id,sr.pricelist_id,company_id
				) AS sr
			LEFT JOIN (SELECT 
					so_line.product_id, 
					so.user_id,
					so.company_id,
					sum(so_line.discount_fixed_line) as discount_fixed_line 
				FROM sale_order so 
				LEFT JOIN  sale_order_line so_line ON so_line.order_id = so.id
				WHERE so.state = 'done' AND so.order_pickup_method_id = 2 AND so_line.is_reward_line = False
				GROUP BY so_line.product_id, so.user_id,so.company_id
				) AS sr_ambil ON sr.product_id = sr_ambil.product_id AND sr.user_id = sr_ambil.user_id AND sr.company_id = sr_ambil.company_id
			LEFT JOIN (SELECT 
					so_line.product_id, 
					so.user_id,
					so.company_id,
					so.pricelist_id,
					sum(so_line.price_subtotal) as price_subtotal 
				FROM sale_order so 
				LEFT JOIN  sale_order_line so_line ON so_line.order_id = so.id
				JOIN product_pricelist ppl ON so.pricelist_id = ppl.id
				JOIN product_pricelist_item ppl_item ON ppl_item.pricelist_id = ppl.id AND ppl_item.product_id = so_line.product_id
				WHERE so.state = 'done' AND so_line.is_reward_line=True
				GROUP BY so_line.product_id, so.user_id,so.company_id,so.pricelist_id,ppl_item.fixed_price
				) AS so_line_promosi ON sr.product_id = so_line_promosi.product_id AND sr.user_id = so_line_promosi.user_id AND sr.company_id = so_line_promosi.company_id
			LEFT JOIN (SELECT 
					so_line.product_id, 
					so.user_id,
					so.company_id,
					sum(so_line.discount_fixed_line) as discount_fixed_line 
				FROM sale_order so 
				LEFT JOIN  sale_order_line so_line ON so_line.order_id = so.id
				WHERE so.state = 'done' AND so_line.is_reward_line = False
				GROUP BY so_line.product_id, so.user_id,so.company_id
				) AS so_line_dt ON sr.product_id = so_line_dt.product_id AND sr.user_id = so_line_dt.user_id AND sr.company_id = so_line_dt.company_id
			LEFT JOIN sales_user_target sut ON sr.user_id = sut.user_id AND sr.year::TEXT = sut.year AND sr.month::TEXT = sut.month
			LEFT JOIN sales_user_target_line sut_line ON sut_line.target_id = sut.id AND sut_line.product_id = sr.product_id 
			JOIN product_product pp ON sr.product_id = pp.id
			JOIN product_template pt ON pp.product_tmpl_id = pt.id
			JOIN product_category pc ON pt.categ_id = pc.id
			WHERE pc.finish_good = True AND sr.user_id = %s AND sr.company_id = %s AND sr.year = %s AND sr.month = %s AND sr.team_id IN %s
			GROUP BY pt.name
			ORDER BY pt.name;
		"""
		team_ids = False
		if self.team_ids:
			team_ids = self.team_ids.ids
		else:
			team_ids = self.user_id.sale_team_ids.ids
		self._cr.execute(query, (self.user_id.id,self.company_id.id,self.year,self.month,tuple(team_ids)))
		res = self._cr.dictfetchall()
		return res

	def _get_expenses(self):
		query = """
		SELECT aa.name AS name, sum(aml.balance) AS balance 
		FROM account_move am
		JOIN account_move_line aml ON aml.move_id = am.id
		JOIN account_account aa ON aml.account_id = aa.id
		WHERE am.state = 'posted' AND aa.user_type_id = 15 AND am.company_id = %s AND EXTRACT(MONTH from am.date)::TEXT = %s AND EXTRACT(YEAR from am.date)::TEXT = %s
		GROUP BY  aa.name;
		"""
		self._cr.execute(query, (self.company_id.id,self.month,self.year,))
		res = self._cr.dictfetchall()
		return res

	def generate_excel(self,data):
		""" Generate excel based from sale.report record. """
		fp = BytesIO()
		workbook = xlsxwriter.Workbook(fp)
		worksheet = workbook.add_worksheet()

		# ========== Format ==============
		header_top_table = workbook.add_format({'bold':True,'valign':'vcenter','align':'center','text_wrap':True})
		header_top_table.set_font_size(10)
		header_top_table.set_font_name('Times New Roman')

		header_table = workbook.add_format({'bold':True,'valign':'vcenter','align':'left','text_wrap':True})
		header_table.set_font_size(10)
		header_table.set_font_name('Times New Roman')

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


		# ========== Header ==============
		divisions_ids = set(self.team_ids.mapped('name'))
		divisions = ','.join(list(divisions_ids))
		worksheet.write(0, 2, 'PERFORMA SALESMAN',header_top_table)
		worksheet.write(1, 2, ('Kode Sales: %s') % (self.user_id.code or ''),header_table)
		worksheet.write(2, 2, ('Nama Sales: %s') % (self.user_id.name or ''),header_table)
		worksheet.write(3, 2, ('Periode   : %s %s') % (MONTH[int(self.month)-1][1],self.year),header_table)
		worksheet.write(4, 2, ('Divisi   : %s')  % (divisions),header_table)
		worksheet.merge_range('B6:B7', 'No.',header_top_table)
		worksheet.merge_range('C6:C7', 'Keterangan',header_top_table)
		worksheet.write(7, 1, 'I',header_top_table)
		worksheet.write(8, 1, 'II',header_top_table)
		worksheet.write(9, 1, 'III',header_top_table)
		worksheet.write(10, 1, 'IV',header_top_table)
		worksheet.write(11, 1, 'V',header_top_table)
		worksheet.write(12, 1, 'VI',header_top_table)
		worksheet.write(13, 1, 'VII',header_top_table)
		worksheet.write(14, 1, 'VIII',header_top_table)
		worksheet.write(15, 1, 'IX',header_top_table)
		worksheet.write(16, 1, 'X',header_top_table)
		worksheet.write(17, 1, 'XI',header_top_table)
		worksheet.write(18, 1, 'XII',header_top_table)
		worksheet.write(19, 1, 'XIII',header_top_table)

		worksheet.write(7, 2, 'TARGET',header_table)
		worksheet.write(8, 2, 'REALISASI QTY',header_table)
		worksheet.write(9, 2, 'PENCAPAIAN %',header_table)
		worksheet.write(10, 2, 'REALISASI VALUE',header_table)
		worksheet.write(11, 2, 'REALISASI POTONGAN AMBIL',header_table)
		worksheet.write(12, 2, 'REALISASI POTONGAN PROGRAM PROMOSI',header_table)
		worksheet.write(13, 2, 'REALISASI POTONGAN PROGRAM POTONGAN DT & BA',header_table)
		worksheet.write(14, 2, 'OMSET NETT VALUE',header_table)
		worksheet.write(15, 2, 'HPP',header_table)
		worksheet.write(16, 2, 'MARGIN KOTOR',header_table)
		worksheet.write(17, 2, 'BIAYA LAINNYA',header_table)
		worksheet.write(18, 2, 'MARGIN PENJUALAN',header_table)
		worksheet.write(19, 2, 'BIAYA OPERASIONAL',header_table)

		col = 3
		row = 5
		row_detail = row + 2
		row_expense = 0
		sum_target = []
		sum_realisasi_qty = []
		sum_achivementt = []
		sum_price_subtotal = []
		sum_potongan_ambil = []
		sum_potongan_promosi = []
		sum_potongan_dt = []
		sum_omset_nett = []
		sum_hpp = []
		sum_margin_kotor = []
		sum_margin_penjualan = []
		for product, data_product in groupby(list(data), lambda product: product.get('name')):
			worksheet.merge_range(row,col,row+1,col, product ,header_top_table)
			for rec in data_product:
				if rec.get('name') == product:
					worksheet.write(row_detail, col, rec.get('target_qty') or 0.00,body_right_table)
					worksheet.write(row_detail + 1, col, rec.get('realisasi_qty') or 0.00,body_right_table)
					worksheet.write(row_detail + 2, col, rec.get('achivement') or 0.00,body_right_table)
					worksheet.write(row_detail + 3, col, rec.get('price_subtotal') or 0.00,body_right_table)
					worksheet.write(row_detail + 4, col, rec.get('potongan_ambil') or 0.00,body_right_table)
					worksheet.write(row_detail + 5, col, rec.get('potongan_promosi') or 0.00,body_right_table)
					worksheet.write(row_detail + 6, col, rec.get('potongan_dt') or 0.00,body_right_table)
					worksheet.write(row_detail + 7, col, rec.get('omset_nett') or 0.00,body_right_table)
					hpp = (self.hpp_percent_factor1/100*float(rec.get('realisasi_qty'))* self.hpp_percent_factor1) + (self.hpp_percent_factor2/100*float(rec.get('realisasi_qty'))* self.hpp_percent_factor2)
					worksheet.write(row_detail + 8, col, hpp or 0.00,body_right_table)
					margin_kotor = (float(rec.get('omset_nett')) - hpp)
					worksheet.write(row_detail + 9, col,  margin_kotor or 0.00,body_right_table)
					worksheet.write(row_detail + 10, col,  0.00,body_right_table)
					margin_penjualan = margin_kotor - 0.00
					worksheet.write(row_detail + 11, col,  margin_penjualan or 0.00,body_right_table)
					# ========== summary total ========== 
					sum_target.append(rec.get('target_qty') or 0.00)
					sum_realisasi_qty.append(rec.get('realisasi_qty') or 0.00)
					sum_achivementt.append(rec.get('achivement') or 0.00)
					sum_price_subtotal.append(rec.get('price_subtotal') or 0.00)
					sum_potongan_ambil.append(rec.get('potongan_ambil') or 0.00)
					sum_potongan_promosi.append(rec.get('potongan_promosi') or 0.00)
					sum_potongan_dt.append(rec.get('potongan_dt') or 0.00)
					sum_omset_nett.append(rec.get('omset_nett') or 0.00)
					sum_hpp.append(hpp or 0.00)
					sum_margin_kotor.append(margin_kotor or 0.00)
					sum_margin_penjualan.append(margin_penjualan or 0.00)
			col = col + 1
		# ========== total ==========
		worksheet.merge_range(row,col,row+1,col, 'Total' ,header_top_table)
		worksheet.write(row_detail, col, sum(sum_target) or 0.00,body_right_table)
		worksheet.write(row_detail + 1, col, sum(sum_realisasi_qty) or 0.00,body_right_table)
		worksheet.write(row_detail + 2, col, sum(sum_achivementt) or 0.00,body_right_table)
		worksheet.write(row_detail + 3, col, sum(sum_price_subtotal) or 0.00,body_right_table)
		worksheet.write(row_detail + 4, col, sum(sum_potongan_ambil) or 0.00,body_right_table)
		worksheet.write(row_detail + 5, col, sum(sum_potongan_promosi) or 0.00,body_right_table)
		worksheet.write(row_detail + 6, col, sum(sum_potongan_dt) or 0.00,body_right_table)
		worksheet.write(row_detail + 7, col, sum(sum_omset_nett) or 0.00,body_right_table)
		worksheet.write(row_detail + 8, col, sum(sum_hpp) or 0.00,body_right_table)
		worksheet.write(row_detail + 9, col, sum(sum_margin_kotor) or 0.00,body_right_table)
		worksheet.write(row_detail + 10, col, 0.00,body_right_table)
		worksheet.write(row_detail + 11, col, sum(sum_margin_penjualan) or 0.00,body_right_table)
		
		row_expense = row_detail + 12
		sum_expense = []
		for expense in self._get_expenses():
			worksheet.write(row_expense + 1, 2, expense.get('name') or 0.00,body_right_table)
			worksheet.write(row_expense + 1, col, expense.get('balance') or 0.00,body_right_table)
			sum_expense.append(expense.get('balance') or 0.00)
			row_expense = row_expense + 1

		worksheet.write(row_expense, col, sum(sum_expense) or 0.00,body_right_table)
		margin_nett = sum(sum_margin_penjualan) - sum(sum_expense)
		worksheet.write(row_expense+1, col, margin_nett or 0.00,body_right_table)
		
		worksheet.write(row_expense+1, 1, 'XIV',header_top_table)
		worksheet.write(row_expense+1, 2, 'MARGIN NETT',header_table)
		
		
		worksheet.set_column('C:C', 40)
		worksheet.set_column(3,col, 15)

		workbook.close()
		out = base64.b64encode(fp.getvalue())
		fp.close()
		filename = ('sale_margin_analysis_report_%s_%s_%s.xlsx') % (self.company_id.name,self.month,self.year )
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