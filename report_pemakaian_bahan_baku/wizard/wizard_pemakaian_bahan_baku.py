from odoo import api, fields, models, tools
import logging
_logger = logging.getLogger(__name__)
import base64
from datetime import date
from io import BytesIO
from calendar import monthrange

try:
	from odoo.tools.misc import xlsxwriter
except ImportError:
	import xlsxwriter


class WizardEnergyConsumptionReport(models.TransientModel):
	_name = 'wizard.pemakaian.bahan.baku.report'
	_description = 'Wizard Pemakaian Bahan Baku Report'

	start_date = fields.Date(string='Start Date', required=True)
	end_date = fields.Date(string='End Date', required=True)
	company_id = fields.Many2one('res.company',
								 string='Company',
								 required=True, default=lambda self: self.env.company)
	name = fields.Char(string="Filename", readonly=True)
	data_file = fields.Binary(string="File", readonly=True)

	def button_print(self):
		data = []
		return self.generate_excel(data)

	# def _get_data_kwh(self):
    # 		query = """
	# 		SELECT 
	# 			date,
	# 			sum(lwbp) AS lwbp,
	# 			sum(bwp) AS bwp,
	# 			sum(kvarh) as kvarh,
	# 			sum(lwbp_bwp) AS lwbp_bwp,
	# 			sum(kwh_terpakai_di_meteran_pln) AS kwh_terpakai 
	# 		FROM 
	# 			mrp_kwh 
	# 		WHERE 
	# 				company_id = %s
	# 			AND
	# 				state = 'submit'
	# 		GROUP BY 
	# 			date 
	# 		ORDER BY 
	# 			date ASC;
	# 	"""
	# 	self._cr.execute(query, (self.company_id.id, ))
	# 	res = self._cr.dictfetchall()
	# 	return res

	def _get_data_material(self):
		query = """
			SELECT 
				date(mp.date_deadline) AS date_deadline,
				pp.default_code as product_code,
				pt.name,
				mm.name as mesin
			FROM 
				mrp_production mp
				LEFT JOIN mrp_mesin mm ON mm.id = mp.mesin_id
				LEFT JOIN stock_move sm ON (sm.production_id = mp.id or sm.raw_material_production_id = mp.id)
				LEFT JOIN product_product pp ON sm.product_id = pp.id
				LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
			WHERE 
				mp.company_id = %s
				AND mp.state in ('done', 'waiting_qc', 'qc_done')
				AND date(mp.date_deadline) <= %s
				AND date(mp.date_deadline) >= %s
			GROUP BY 
				date(mp.date_deadline),pp.default_code,pt.name,mm.name
			ORDER BY date(mp.date_deadline) ASC;
		"""
		self._cr.execute(query, (self.company_id.id, self.start_date, self.end_date))
		res = self._cr.dictfetchall()
		return res

	# def _calculate_total_per_mesin(self, month, name):
	# 	rh = 0
	# 	kwh = 0
	# 	production = 0
	# 	type_mesin = ''
	# 	for rec in self._get_data_mesin():
	# 		if rec.get('name') == name:
	# 			if rec.get('date_deadline'):
	# 				if rec.get('date_deadline').month == month:
	# 					rh = rh + rec.get('rh')
	# 					kwh = kwh + rec.get('kwh')
	# 					production = production + rec.get('production')
	# 			type_mesin = rec.get('type_mesin')

	# 	return {
	# 		'production':production,
	# 		'rh':rh,
	# 		'kwh':kwh,
	# 		'type_mesin':type_mesin,
	# 	}

	def generate_excel(self, data):
		""" Generate excel based from label.print record. """
		MONTH = [
			'JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS', 'SEPT',
			'OKT', 'NOV', 'DES'
		]
		fp = BytesIO()
		workbook = xlsxwriter.Workbook(fp)
		worksheet = workbook.add_worksheet()
		
		# ========== Format ==============
		header_table = workbook.add_format({'bold':True,'valign':'vcenter','align':'center','text_wrap':True})
		header_table.set_border()

		body_table = workbook.add_format()
		body_table.set_align('right')
		body_table.set_align('vcenter')
		body_table.set_border()
		body_table.set_num_format('#,##0')

		body_table_des = workbook.add_format()
		body_table_des.set_align('right')
		body_table_des.set_align('vcenter')
		body_table_des.set_border()
		body_table_des.set_num_format('#,##0.#0')

		worksheet.set_column('D:E', 25)
		worksheet.set_column('G:H', 30)

		# ========== HEADER STATIS ==============
		worksheet.merge_range('A2:R2', 'Report Transaksi Material Tahun :' + str(self.start_date) + ' s/d ' + str(self.end_date))
		worksheet.merge_range('A4:A5', 'Tanggal', header_table)
		worksheet.merge_range('B4:B5', 'Kode Barang', header_table)
		worksheet.merge_range('C4:C5', 'Nama Barang', header_table)
		worksheet.merge_range('D4:D5', 'Saldo Awal', header_table)
		worksheet.merge_range('E4:E5', 'Masuk dari WHM', header_table)
		worksheet.merge_range('F4:F5',
							  'Masuk dari Produksi', header_table)
		worksheet.merge_range('G4:G5',
							  'Pemakaian', header_table)
		worksheet.merge_range('H4:H5',
							  'Rijek Produksi (Rijek Dilimbahkan)', header_table)
		worksheet.merge_range('I4:I5',
							  'Rijek Supplier(Rijek Di daur ulang)', header_table)
		worksheet.merge_range('J4:J5',
							  'Return/Kirim', header_table)
		worksheet.merge_range('K4:K5',
							  'Jumlah Keluar', header_table)
		worksheet.merge_range('L4:L5',
							  'Saldo Akhir', header_table)
		worksheet.merge_range('M4:M5',
							  'Mesin', header_table)
		worksheet.merge_range('N4:N5',
							  'Shift', header_table)
		worksheet.merge_range('O4:O5',
							  'User', header_table)
		worksheet.merge_range('P4:P5',
							  'Jumlah Keluar', header_table)
		worksheet.merge_range('Q4:Q5',
							  'No Batch / Lot Pemakaian BBK', header_table)
		worksheet.merge_range('R4:R5',
							  'Prosentase rijek Produksi', header_table)
		
		# data_kwh = self._get_data_kwh()
		# data_mesin = self._get_data_mesin()
		master_mesin = self.env['mrp.mesin'].search([('company_id','=',self.company_id.id)])
		row = 5
		first_col_total = 0
		last_col_total = first_col_total + 0
		# ========== BODY ==============
		# ========== Looping day in month ==============
		data = self._get_data_material()
		for material in data:
			worksheet.write(row, 1, material.get('date_deadline'), header_table)
			worksheet.write(row, 2, material.get('product_code'), header_table)
			# worksheet.write(row, 3, '-', body_table)
			# worksheet.write(row, 4, '-', body_table)
			# worksheet.write(row, 5, '-', body_table)
			# worksheet.write(row, 6, '-', body_table)
			# worksheet.write(row, 7,'-', body_table)
			# # ========== Looping KWH ==============
			# for kwh in data_kwh:
			# 	if kwh.get('date'):
			# 		if kwh.get('date') == date(self.start_date.year, month,
			# 									day):
			# 			worksheet.write(row, 3, kwh.get('lwbp') or '-', body_table_des)
			# 			worksheet.write(row, 4, kwh.get('bwp') or '-', body_table_des)
			# 			worksheet.write(row, 5, kwh.get('kvarh') or '-', body_table_des)
			# 			worksheet.write(row, 6, kwh.get('lwbp_bwp') or '-', body_table_des)
			# 			worksheet.write(
			# 				row, 7,
			# 				kwh.get('kwh_terpakai') * float(self.kwh_meter)
			# 				or '-', body_table_des)
			# 			total_lwbp = total_lwbp + kwh.get('lwbp')
			# 			total_bwp = total_bwp + kwh.get('bwp')
			# 			total_kvarh = total_kvarh + kwh.get('kvarh')
			# 			total_lwbp_bwp = total_lwbp_bwp + kwh.get('lwbp_bwp')
			# 			total_kwh_terpakai = total_kwh_terpakai + (kwh.get('kwh_terpakai') * float(self.k
			

		workbook.close()
		out = base64.b64encode(fp.getvalue())
		fp.close()
		filename = ('laporan_pemakaian_bahan_baku.xlsx')
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