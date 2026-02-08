# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
import logging
_logger = logging.getLogger(__name__)
import base64
from datetime import date
from io import BytesIO
from calendar import monthrange
from datetime import date, datetime

try:
	from odoo.tools.misc import xlsxwriter
except ImportError:
	import xlsxwriter


class WizardMonthlyProductionPlanReport(models.TransientModel):
	_name = 'wizard.monthly.production.plan.report'
	_description = 'Wizard Monthly Production Plan Report'

	YEARS = [(str(num), str(num)) for num in range(2020, (datetime.now().year)+10 )]
 
	year = fields.Selection(YEARS, string='Periode',required=True)

	month = fields.Selection([('1', 'January'), ('2', 'February'), ('3', 'March'),
			  ('4', 'April'), ('5', 'May'), ('6', 'June'), ('7', 'July'),
			  ('8', 'August'), ('9', 'September'), ('10', 'October'),
			  ('11', 'November'), ('12', 'December')], string='Month', required=True)
	company_id = fields.Many2one('res.company',
								 string='Company',
								 required=True, default=lambda self: self.env.company)
	name = fields.Char(string="Filename", readonly=True)
	data_file = fields.Binary(string="File", readonly=True)

	def button_print(self):
		data = self._get_data_product()
		return self.generate_excel(data)

	def _get_data_product(self):
		query = """
			SELECT 
				product_classification AS class,
				name AS name
			FROM 
				product_template
			GROUP BY 
				product_classification,
				name
			ORDER BY 
				product_classification,
				name;
		"""
		self._cr.execute(query)
		res = self._cr.dictfetchall()
		return res
	
	def _get_week(self):
		first_week = date(int(self.year),int(self.month),1).isocalendar()[1]
		last_week = date(int(self.year),int(self.month),monthrange(int(self.year),int(self.month))[1]).isocalendar()[1]
		return [first_week,last_week]

	def _get_data_mrp(self):
		query = """
			SELECT 
				mrp.week AS week,mrp.name AS name,mrp.qty_target AS qty_target, sm.qty_realisasi AS qty_realisasi, mrp.company_id, sm.company_id
			FROM 
				(
					SELECT  EXTRACT('week' from mrl.date) as week, pt.name as name, sum(mrl.qty_forecast) as qty_target, mr.company_id as company_id
					FROM mrp_rph mr
					JOIN mrp_rph_line mrl ON mr.id = mrl.mrp_rph_id 
					JOIN product_product pp ON pp.id = mr.product_id
					JOIN product_template pt ON pt.id = pp.product_tmpl_id
					GROUP BY EXTRACT('week' from mrl.date), pt.name, mr.company_id
				) AS mrp
			LEFT JOIN 
				(
					SELECT EXTRACT('week' from sm.date) as week,
					pt.name as name, sm.company_id as company_id, sum(sm.product_uom_qty) as qty_realisasi
					FROM stock_move sm
					JOIN product_product pp ON pp.id = sm.product_id
					JOIN product_template pt ON pt.id = pp.product_tmpl_id
					JOIN stock_location source_sl ON sm.location_id = source_sl.id 
					JOIN Stock_location source_p_sl ON source_sl.location_id = source_p_sl.id
					JOIN stock_location dest_sl ON sm.location_dest_id = dest_sl.id 
					WHERE source_p_sl.usage = 'view' 
					AND source_p_sl.location_id is null 
					AND source_sl.usage = 'production'
					AND dest_sl.production_for_pbbh = True
					AND dest_sl.usage = 'internal'
					AND sm.state = 'done'
					GROUP BY EXTRACT('week' from sm.date), pt.name, sm.company_id
				) AS sm ON sm.name = mrp.name AND mrp.name = sm.name AND mrp.week = sm.week AND mrp.company_id = sm.company_id
			WHERE mrp.company_id = %s AND mrp.week BETWEEN %s AND %s
			ORDER BY mrp.week,mrp.name;
		"""
		week = self._get_week()
		self._cr.execute(query,
						 (self.company_id.id, week[0],week[1]))
		res = self._cr.dictfetchall()
		return res

	def generate_excel(self, data):
		""" Generate excel based from purchase.order record. """
		fp = BytesIO()
		workbook = xlsxwriter.Workbook(fp)
		worksheet = workbook.add_worksheet()

		# ========== Format ==============
		header_table = workbook.add_format({
			'bold': True,
			'valign': 'vcenter',
			'align': 'center',
			'text_wrap': True
		})
		header_table.set_font_size(12)
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

		worksheet.set_column('B:B', 25)


		# ========== Header ==============
		worksheet.merge_range('E3:Q3', 'Rencana Produksi Bulanan',
							  header_table)
		worksheet.merge_range('C4:E4', (_('Bulan %s %s') %
										(str(date(int(self.year),int(self.month),1).month),str(self.year))),
							  header_table)

		# ========== Header Product ==============
		worksheet.merge_range('B5:B6', 'Nama Produk', header_table)
		data_mrp = self._get_data_mrp()

		row = 8
		name_class = ''
		for rec in data:
			row_subtotal = ''
			if name_class == '':
				name_class = rec.get('class')
				row = row + 1
				row_subtotal = row
			elif name_class != rec.get('class'):
				worksheet.write(
				    ('B%s') % (row),
				    ('JUMLAH'),
				    header_table)
				name_class = rec.get('class')
				row_subtotal = row
				row = row + 2
			if name_class == rec.get('class'):
				worksheet.write(
						('B%s') % (row),
						('%s') % (rec.get('name') or '-'),
						body_table)
				first_col = 2
				x = 1
				week_number = ''
				row_mrp = row - 1
				subtotal_target_per_week = 0
				subtotal_realisasi_per_week = 0 
				for mrp in data_mrp:
					if week_number != mrp.get('week'):
						worksheet.merge_range(4, first_col, 4, first_col+2, ('MINGGU %s')%(x) , header_table)
						worksheet.write(5, first_col, 'Target', header_table)
						worksheet.write(5, first_col + 1, 'Realisasi', header_table)
						worksheet.write(5, first_col + 2, '%', header_table)
						worksheet.write(row_mrp, first_col, '-', body_right_table)
						worksheet.write(row_mrp, first_col + 1, '-', body_right_table)
						worksheet.write(row_mrp, first_col + 2, '-', body_right_table)
						week_number = mrp.get('week')
						x = x + 1
					if rec.get('name') == mrp.get('name'):
						worksheet.write(row_mrp, first_col, mrp.get('qty_target') or '-', body_right_table)
						worksheet.write(row_mrp, first_col + 1, mrp.get('qty_realisasi') or '-', body_right_table)
						worksheet.write(row_mrp, first_col + 2, '-', body_right_table)
						first_col = first_col + 3
						subtotal_target_per_week = subtotal_target_per_week + mrp.get('qty_target') if mrp.get('qty_target') else 0.0
						subtotal_realisasi_per_week = subtotal_realisasi_per_week + mrp.get('qty_realisasi') if mrp.get('qty_realisasi') else 0.0
						# worksheet.write(row_subtotal, first_col, subtotal_target_per_week or '-', body_right_table)
						# worksheet.write(row_subtotal, first_col + 1, subtotal_realisasi_per_week or '-', body_right_table)
						# worksheet.write(row_subtotal, first_col + 2, '-', body_right_table)
			row = row + 1
		worksheet.write(
				    ('B%s') % (row),
				    ('JUMLAH'),
				    header_table)

		workbook.close()
		out = base64.b64encode(fp.getvalue())
		fp.close()
		filename = ('monthly_production_plan_%s_%s_%s.xlsx') % (
			self.company_id.name, self.year, self.month)
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
