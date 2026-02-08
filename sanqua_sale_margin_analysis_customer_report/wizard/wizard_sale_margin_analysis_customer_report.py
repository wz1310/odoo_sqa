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

class WizardSaleMarginAnalysisCustomerReport(models.TransientModel):
	_name = 'wizard.sale.margin.analysis.customer.report'
	_description = 'Wizard Sale Margin Analysis Customer Report'

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
				SELECT pt.default_code AS code, 
					pt.name AS product_name,
					rp.name as partner_name
					, sum(sut_line.qty) AS target_qty
					, sum(sr.qty_delivered) AS realisasi_qty
					, (sum(sr.qty_delivered) / sum(sut_line.qty)) * 100 AS achivement
					, sum(sr.price_subtotal) AS price_subtotal
					, sum(sr_ambil.discount_fixed_line) AS potongan_ambil
					, sum(so_line_promosi.price_subtotal) AS potongan_promosi
					, sum(so_line_dt.discount_fixed_line) AS potongan_dt
					, COALESCE(sum(sr.price_subtotal),0) - COALESCE(sum(sr_ambil.discount_fixed_line),0) - COALESCE(sum(so_line_promosi.price_subtotal),0) - COALESCE(sum(so_line_dt.discount_fixed_line),0) AS omset_nett
					, (%s * sum(sr.qty_delivered)*%s) + (%s * sum(sr.qty_delivered)* %s) AS hpp
				, (COALESCE(sum(sr.price_subtotal),0) - COALESCE(sum(sr_ambil.discount_fixed_line),0) - COALESCE(sum(so_line_promosi.price_subtotal),0) - COALESCE(sum(so_line_dt.discount_fixed_line),0)) - ((%s * sum(sr.qty_delivered)*%s) + (%s * sum(sr.qty_delivered)* %s)) AS margin_kotor
				FROM (SELECT 
						product_id, 
						user_id,
						team_id,
					partner_id,
						EXTRACT(MONTH from date) AS month,
						EXTRACT(YEAR from date) AS year,
						company_id,
						sr.pricelist_id,
						sum(qty_delivered) as qty_delivered,
						sum(price_subtotal) as price_subtotal 
					FROM sale_report sr
					WHERE state = 'done'
					GROUP BY partner_id,product_id, user_id,sr.pricelist_id,company_id,
						EXTRACT(MONTH from date),
						EXTRACT(YEAR from date),team_id
					ORDER BY partner_id,product_id, user_id,sr.pricelist_id,company_id
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
				JOIN res_partner rp ON sr.partner_id = rp.id
				WHERE pc.finish_good = True AND sr.user_id = %s AND sr.company_id = %s AND sr.year = %s AND sr.month = %s
				
		"""
		team_ids = False
		if self.team_ids:
			team_ids = self.team_ids.ids
		else:
			team_ids = self.user_id.sale_team_ids.ids
		hpp_1 = (self.hpp_percent_factor1/100)
		hpp_2 = (self.hpp_percent_factor2/100)
		
		params = (hpp_1, self.hpp_amount_factor1, hpp_2,self.hpp_amount_factor2, hpp_1, self.hpp_amount_factor1, hpp_2,self.hpp_amount_factor2,
			self.user_id.id,self.company_id.id,self.year,self.month)
		team_conditions = "AND sr.team_id IN %s" % (tuple(team_ids),)

		if not len(team_ids):
			team_conditions = ""

		if len(team_conditions):
			query += team_conditions
			# params+=(team_conditions,)

		query += """GROUP BY pt.default_code,pt.name,rp.name
				ORDER BY pt.default_code,pt.name,rp.name"""

		self._cr.execute(query, params)
		
		res = self._cr.dictfetchall()
		return res

	def _grouping_by_partner(self,data,list_partner):
		for partner, data_partner in groupby(list(data), lambda partner: partner.get('partner_name')):
			if partner not in list_partner:
				list_partner.append(partner)
		return list_partner

	def _write_excel_by_partner(self,list_partner,row,col,data,worksheet,header_top_table,header_top_right_table,header_table,body_right_table,header_text,value,first_row=False,print_value=True):
		sum_target = [] 
		col = col
		if first_row:
			worksheet.merge_range(7, 2, 7, 3, header_text,header_table)
		else:
			worksheet.merge_range(row, 2, row, 3, header_text,header_table)
		row_temp = sum_target = 11
		for partner in list_partner:
			sum_per_partner = []
			row_partner = row + 1 
			count = 1
			for target in data:
				if print_value:
					worksheet.write(row_partner, 1, count,header_top_table)
					worksheet.write(row_partner, 2, target.get('code') or '',header_table)
					worksheet.write(row_partner, 3, target.get('product_name') or '',header_table)
				if target.get('partner_name') == partner:
					if print_value:
						worksheet.write(row_partner, col, target.get(value) or 0.00,body_right_table)
					sum_per_partner.append(target.get(value) or 0.00)
				else:
					if print_value:
						worksheet.write(row_partner, col, '-',body_right_table)
				if print_value:
					row_partner = row_partner + 1
					count = count + 1
			worksheet.merge_range(row_partner, 2,row_partner, 3,  'TOTAL',header_top_table)
			worksheet.write(row_partner, col, sum(sum_per_partner) or 0.00,header_top_right_table)
			sum_target.append({'name':partner,'total':sum(sum_per_partner),'category':header_text})
			col = col + 1
			row_temp = row_partner + 1
		return [row_temp,sum_target]

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

		header_top_right_table = workbook.add_format({'bold':True,'valign':'vcenter','align':'center','text_wrap':True})
		header_top_right_table.set_font_size(10)
		header_top_right_table.set_font_name('Times New Roman')
		header_top_right_table.set_num_format('#,##0.00')

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
		worksheet.merge_range('C6:D7', 'Keterangan',header_top_table)
		
		list_partner = []
		list_partner = self._grouping_by_partner(data,list_partner)

		col = 4
		row = 5
		for partner in list_partner:
			worksheet.merge_range(row,col,row+1,col, partner ,header_top_table)
			col = col + 1
		# ========== TARGET Quantity ==========
		row_temp, sum_target = self._write_excel_by_partner(list_partner,7,4,data,worksheet,header_top_table,header_top_right_table,header_table,body_right_table,'I. Target','target_qty',first_row=True)
		# ========== REALISASI Quantity ==========
		row_temp, sum_realisasi_qty = self._write_excel_by_partner(list_partner,row_temp,4,data,worksheet,header_top_table,header_top_right_table,header_table,body_right_table,'II. REALISASI QTY','realisasi_qty')
		# ========== Pencapaian ==========
		col = 4
		worksheet.merge_range(row_temp, 2, row_temp, 3, 'III. PENCAPAIAN (%)',header_table)
		for partner in list_partner:
			for realisasi in sum_realisasi_qty:
				for target in sum_target:
					if realisasi.get('name')  == partner and target.get('name') == partner:
						sum_total = (realisasi.get('total') / target.get('total')) * 100 if target.get('total') > 0 else 0.00
						worksheet.write(row_temp, col, "{:.2f}".format(round(sum_total, 2)) + ' %',header_top_right_table)
						col = col + 1
		# ========== REALISASI Value ==========
		row_temp, sum_value = self._write_excel_by_partner(list_partner,row_temp+1,4,data,worksheet,header_top_table,header_top_right_table,header_table,body_right_table,'IV. REALISASI VALUE','price_subtotal')
		# ========== REALISASI POTONGAN AMBIL ==========
		row_temp, sum_potongan_ambil = self._write_excel_by_partner(list_partner,row_temp,4,data,worksheet,header_top_table,header_top_right_table,header_table,body_right_table,'V. REALISASI POTONGAN AMBIL','potongan_ambil')
		# ========== REALISASI POTONGAN PROMOSI ==========
		row_temp, sum_potongan_promosi = self._write_excel_by_partner(list_partner,row_temp,4,data,worksheet,header_top_table,header_top_right_table,header_table,body_right_table,'VI. REALISASI POTONGAN PROGRAM PROMOSI','potongan_promosi')
		# ========== REALISASI POTONGAN DT ==========
		row_temp, sum_potongan_dt = self._write_excel_by_partner(list_partner,row_temp,4,data,worksheet,header_top_table,header_top_right_table,header_table,body_right_table,'VII. REALISASI POTONGAN PROGRAM POTONGAN DT & BA','potongan_dt')
		# ========== OMSET NETT VALUE ==========
		row_temp, sum_omset = self._write_excel_by_partner(list_partner,row_temp,4,data,worksheet,header_top_table,header_top_right_table,header_table,body_right_table,'VIII. OMSET NETT VALUE','omset_nett')
		# ========== HPP ==========
		row_temp, sum_hpp = self._write_excel_by_partner(list_partner,row_temp,4,data,worksheet,header_top_table,header_top_right_table,header_table,body_right_table,'IX. HPP','hpp')
		# ========== MARGIN KOTOR ==========
		row_temp, sum_margin_kotor = self._write_excel_by_partner(list_partner,row_temp,4,data,worksheet,header_top_table,header_top_right_table,header_table,body_right_table,'X. MARGIN KOTOR','margin_kotor')
		# ========== Biaya Lainnya ==========
		row_temp, sum_biaya_lainnya = self._write_excel_by_partner(list_partner,row_temp,4,data,worksheet,header_top_table,header_top_right_table,header_table,body_right_table,'XI. BIAYA LAINNYA','-',print_value=False)
		# ========== MARGIN NETT ==========
		col = 4
		worksheet.merge_range(row_temp, 2, row_temp, 3, 'XII. MARGIN NET',header_table)
		for partner in list_partner:
			for margin in sum_margin_kotor:
				for biaya in sum_biaya_lainnya:
					if margin.get('name')  == partner and biaya.get('name') == partner:
						sum_total = margin.get('total') - biaya.get('total')
						worksheet.write(row_temp, col, sum_total,header_top_right_table)
						col = col + 1

		worksheet.set_column('C:D', 20)
		worksheet.set_column(3,col, 15)

		workbook.close()
		out = base64.b64encode(fp.getvalue())
		fp.close()
		filename = ('sale_margin_analysis_customer_report_%s_%s_%s.xlsx') % (self.company_id.name,self.month,self.year )
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