# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
try:
	from odoo.tools.misc import xlsxwriter
except ImportError:
	import xlsxwriter

import base64
from datetime import datetime
from io import BytesIO
from calendar import monthrange, monthcalendar

_logger = logging.getLogger(__name__)

MONTH = [('1', 'January'), ('2', 'February'), ('3', 'March'),
			  ('4', 'April'), ('5', 'May'), ('6', 'June'), ('7', 'July'),
			  ('8', 'August'), ('9', 'September'), ('10', 'October'),
			  ('11', 'November'), ('12', 'December')]

class WeeklySaleRatioReportWizard(models.TransientModel):
	_name = 'weekly.sale.ratio.report.wizard'
	_description = 'Wizard Weekly Sale Ratio Report'
	YEARS = [(str(num), str(num)) for num in range(2020, (datetime.now().year)+1 )]
	
	partner_id = fields.Many2one('res.partner', string='Customer')
	user_id = fields.Many2one('res.users', string='Salesperson')
	year = fields.Selection(YEARS, string='Periode',required=True)
	month = fields.Selection(MONTH, string='Month',required=True)
	name = fields.Char(string="Filename", readonly=True)
	data_file = fields.Binary(string="File", readonly=True)
	factor_day_1 = fields.Float(compute='_compute_factor_day_1', string='Factor 1')
	factor_day_2 = fields.Float(compute='_compute_factor_day_2', string='Factor 2')
	
	@api.depends('month','year')
	def _compute_factor_day_1(self):
		for rec in self:
			if rec.month and rec.year:
				count_sunday = len([1 for i in monthcalendar(int(rec.year),int(rec.month)) if i[6] != 0])
				last_day = monthrange(int(rec.year),int(rec.month))[1]
				rec.factor_day_1 = last_day - count_sunday
			else:
				rec.factor_day_1 = 0.0
	
	@api.depends('month','year')
	def _compute_factor_day_2(self):
		for rec in self:
			if rec.month and rec.year:
				rec.factor_day_2 = datetime.today().day
			else:
				rec.factor_day_2 = 0.0


	def btn_confirm(self):
		query = """
			SELECT  rp.code, 
					rp.name as partner,
					rm.name as region,
					cg.name as class_outlet,
					pt.default_code,
					pt.name as product, 
					COALESCE(sum(sut_line.qty),0) as target_qty,
					sr.periode_1, 
					sr.periode_2, 
					sr.periode_3,
					sr.periode_1 + sr.periode_2 + sr.periode_3 AS total_realisasi, 
					COALESCE(
						(sr.periode_1 + sr.periode_2 + sr.periode_3) - ((sum(sut_line.qty) / %s) * %s),0) AS minus_qty,
					CASE
							WHEN sum(sut_line.qty) > 0 THEN (sr.periode_1 + sr.periode_2 + sr.periode_3) / ((sum(sut_line.qty) / %s) * %s) ELSE 0
					END AS achievement,
					COALESCE((sr.periode_1 + sr.periode_2 + sr.periode_3) - sum(sut_line.qty),0) AS minus_month_qty,
					CASE
							WHEN sum(sut_line.qty) > 0 THEN (sr.periode_1 + sr.periode_2 + sr.periode_3) / sum(sut_line.qty) ELSE 0
					END AS achievement_mont
	   		FROM
				(SELECT sr.user_id,sr.partner_id, rp.region_master_id, ppr.customer_group, sr.product_id, sr.date::DATE,
			 		CASE
	 					WHEN EXTRACT(DAY FROM sr.date::DATE) BETWEEN 1 AND 10  THEN sum(product_uom_qty) ELSE 0
			 		END AS periode_1,
			 		CASE
	 					WHEN EXTRACT(DAY FROM sr.date::DATE) BETWEEN 11 AND 20  THEN sum(product_uom_qty) ELSE 0
			 		END AS periode_2,
			 		CASE
	 					WHEN EXTRACT(DAY FROM sr.date::DATE) BETWEEN 21 AND EXTRACT(DAY FROM (date_trunc('MONTH', sr.date::DATE) + INTERVAL '1 MONTH - 1 day'))  THEN sum(product_uom_qty) ELSE 0
			 		END AS periode_3
				FROM sale_report sr
				JOIN res_partner rp ON rp.id = sr.partner_id
				JOIN partner_pricelist ppr ON ppr.partner_id = rp.id
				GROUP BY sr.user_id,sr.partner_id, rp.region_master_id, ppr.customer_group, sr.product_id,  sr.date::DATE
				ORDER BY sr.partner_id, rp.region_master_id, ppr.customer_group, sr.product_id,  sr.date::DATE
				) AS sr
			LEFT JOIN sales_user_target sut ON sut.user_id = sr.user_id AND EXTRACT(YEAR from sr.date)::TEXT = sut.year AND EXTRACT(MONTH from sr.date)::TEXT = sut.month
			LEFT JOIN sales_user_target_line sut_line ON sut_line.target_id = sut.id AND sut_line.product_id = sr.product_id AND sut_line.partner_id = sr.partner_id
			JOIN res_partner rp ON rp.id = sr.partner_id
			JOIN region_master rm ON rm.id = rp.region_master_id
			JOIN customer_group cg ON cg.id = sr.customer_group
			JOIN product_product pp ON pp.id = sr.product_id
			JOIN product_template pt ON pt.id = pp.product_tmpl_id
			JOIN product_category pc ON pc.id = pt.categ_id
			WHERE 
				EXTRACT(MONTH from sr.date)::TEXT = %s AND 
				EXTRACT(YEAR from sr.date)::TEXT = %s AND
				sr.partner_id IN %s AND
				sr.user_id IN %s AND pc.carton = FALSE
			GROUP BY  rp.code, rp.name,rm.name,pt.default_code,pt.name,sr.periode_1, sr.periode_2, sr.periode_3,sr.date::DATE,cg.name
			ORDER BY  sr.date;
		"""
		partner_ids = self.partner_id.ids
		if not self.partner_id:
			partner_ids = self.env['sale.report'].search([]).mapped('partner_id').ids
		user_ids = self.user_id.ids
		if not self.user_id:
			user_ids = self.env['sale.report'].search([]).mapped('user_id').ids
		self.env.cr.execute(query, (self.factor_day_1,self.factor_day_2,self.factor_day_1,self.factor_day_2 ,self.month,self.year,tuple(partner_ids),tuple(user_ids)))
		query_res = self.env.cr.fetchall()
		return self.generate_excel(query_res)

	
	def generate_excel(self, data):
		""" Generate excel based from label.print record. """
		MONTH = ['JANUARI','FEBRUARI','MARET','APRIL','MEI','JUNI','JULI',
			'AGUSTUS','SEPTEMBER','OKTOBER','NOVEMBER','DESEMBER']
		fp = BytesIO()
		workbook = xlsxwriter.Workbook(fp)
		worksheet = workbook.add_worksheet()

		# =============== HEADER ===============
		header_format = workbook.add_format({'bold': True,'align':'center'})
		center_format = workbook.add_format({'align':'center'})

		body_right_format = workbook.add_format()
		body_right_format.set_align('right')
		body_right_format.set_align('vcenter')
		body_right_format.set_num_format('#,##0.00')

		worksheet.set_column('A4:A4', 15)
		worksheet.set_column('B4:B4', 30)
		worksheet.set_column('C4:C4', 10)
		worksheet.set_column('D4:E4', 15)
		worksheet.set_column('F4:F4', 30)
		worksheet.set_column('G4:R4', 10)
		worksheet.merge_range('A1:R2',('LAPORAN TARGET DAN REALISASI PERMINGGU %s %s') % (str(MONTH[int(self.month)-1]),str(self.year)),header_format)
		worksheet.write(3, 0, "Kode Pelanggan",center_format)
		worksheet.write(3, 1, "Nama Pelanggan",center_format)
		worksheet.write(3, 2, "Area",center_format)
		worksheet.write(3, 3, "Class Outlet",center_format)
		worksheet.write(3, 4, "Kode Barang",center_format)
		worksheet.write(3, 5, "Nama Barang",center_format)
		worksheet.write(3, 6, "Target",center_format)
		worksheet.write(3, 7, "PERIODE 1-10",center_format)
		worksheet.write(3, 8, "TANGGAL 11-20",center_format)
		worksheet.write(3, 9, "TANGGAL 21-31",center_format)
		worksheet.write(3, 10, "TOTAL REALISASI",center_format)
		worksheet.write(3, 11, "Kekurangan",center_format)
		worksheet.write(3, 12, "% PENCAPAIAN",center_format)
		worksheet.write(3, 13, "KEKURANGAN",center_format)
		worksheet.write(3, 14, "% PENCAPAIAN",center_format)
		# =============== HEADER ===============

		# =============== BODY ===============
		format_right = workbook.add_format({'align': 'right'})

		row_idx = 4
		for line in data:
			worksheet.write(row_idx, 0, line[0],center_format)
			worksheet.write(row_idx, 1, line[1])
			worksheet.write(row_idx, 2, line[2])
			worksheet.write(row_idx, 3, line[3],center_format)
			worksheet.write(row_idx, 4, line[4],center_format)
			worksheet.write(row_idx, 5, line[5])
			worksheet.write(row_idx, 6, line[6],body_right_format)
			worksheet.write(row_idx, 7, line[7],body_right_format)
			worksheet.write(row_idx, 8, line[8],body_right_format)
			worksheet.write(row_idx, 9, line[9],body_right_format)
			worksheet.write(row_idx, 10, line[10],body_right_format)
			worksheet.write(row_idx, 11, abs(line[11]),body_right_format)
			worksheet.write(row_idx, 12, line[12],body_right_format)
			worksheet.write(row_idx, 13, abs(line[13]),body_right_format)
			worksheet.write(row_idx, 14, line[14],body_right_format)
			row_idx += 1
		# =============== BODY ===============
		worksheet.set_column('B:B', 40)
		worksheet.set_column('C:C', 25)
		worksheet.set_column('F:F', 40)
		worksheet.set_column('G:O', 15)
		workbook.close()
		out = base64.b64encode(fp.getvalue())
		fp.close()
		filename = ('weekly_sale_ratio_%s.xlsx')%(self.year)
		return self.set_data_excel(out, filename)

	def set_data_excel(self, out, filename):
		""" Update data_file and name based from previous process output. And return action url for download excel. """
		self.write({
			'data_file': out,
			'name': filename
		})

		return {
			'type': 'ir.actions.act_url',
			'name': filename,
			'url': '/web/content/%s/%s/data_file/%s' % (self._name, self.id, filename,),
		}

	