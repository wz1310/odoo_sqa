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
	_name = 'wizard.energy.consumption.report'
	_description = 'Wizard Energy Consumption Report'

	start_date = fields.Date(string='Start Date', required=True)
	end_date = fields.Date(string='End Date', required=True)
	kwh_meter = fields.Integer(string='Kwh/Meter', required=True, default=4000)
	kwh_price = fields.Integer(string='Harga per Kwh', required=True, default=1122)
	company_id = fields.Many2one('res.company',
								 string='Company',
								 required=True, default=lambda self: self.env.company)
	name = fields.Char(string="Filename", readonly=True)
	data_file = fields.Binary(string="File", readonly=True)

	def button_print(self):
		data = []
		return self.generate_excel(data)

	def _get_data_kwh(self):
		query = """
			SELECT 
				date,
				sum(lwbp) AS lwbp,
				sum(bwp) AS bwp,
				sum(kvarh) as kvarh,
				sum(lwbp_bwp) AS lwbp_bwp,
				sum(kwh_terpakai_di_meteran_pln) AS kwh_terpakai 
			FROM 
				mrp_kwh 
			WHERE 
					company_id = %s
				AND
					state = 'submit'
			GROUP BY 
				date 
			ORDER BY 
				date ASC;
		"""
		self._cr.execute(query, (self.company_id.id, ))
		res = self._cr.dictfetchall()
		return res

	def _get_data_mesin(self):
		query = """
			SELECT 
				date(mp.date_deadline) AS date_deadline,
				mm.name AS name,
				sum(mp.total_jam_kerja) AS rh,
				sum(mm.kwh_per_jam) * sum(mp.total_jam_kerja)  AS kwh,
				sum(mp.qty_produced) AS production,
				max(mm.type_mesin) as type_mesin
			FROM 
				mrp_production mp
			LEFT JOIN 
				mrp_mesin mm ON mm.id = mp.mesin_id
			WHERE 
				mp.company_id = %s
				AND mp.state in ('done', 'waiting_qc', 'qc_done')
			GROUP BY 
				mm.name,date(mp.date_deadline)
			ORDER BY date(mp.date_deadline) ASC;
		"""
		self._cr.execute(query, (self.company_id.id, ))
		res = self._cr.dictfetchall()
		return res

	def _calculate_total_per_mesin(self, month, name):
		rh = 0
		kwh = 0
		production = 0
		type_mesin = ''
		for rec in self._get_data_mesin():
			if rec.get('name') == name:
				if rec.get('date_deadline'):
					if rec.get('date_deadline').month == month:
						rh = rh + rec.get('rh')
						kwh = kwh + rec.get('kwh')
						production = production + rec.get('production')
				type_mesin = rec.get('type_mesin')

		return {
			'production':production,
			'rh':rh,
			'kwh':kwh,
			'type_mesin':type_mesin,
		}

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
		worksheet.merge_range('C3:H3', 'Pemakaian Kwh Meter Tahun :')
		worksheet.write('I3', str(self.start_date.year))
		worksheet.merge_range('B4:B5', 'Bulan', header_table)
		worksheet.merge_range('C4:C5', 'Tanggal', header_table)
		worksheet.merge_range('D4:D5', 'KWH Tercatat di Meteran (LWBP)', header_table)
		worksheet.merge_range('E4:E5', 'KWH Tercatat di Meteran (WBP)', header_table)
		worksheet.merge_range('F4:F5', 'kVarh', header_table)
		worksheet.merge_range('G4:G5',
							  'KWH Tercatat di Meteran (LWBP+WBP+kVarh)', header_table)
		worksheet.write('H4', 'KWh Terpakai di Meteran PLN', header_table)
		worksheet.write('H5', str(self.kwh_meter), header_table)

		data_kwh = self._get_data_kwh()
		data_mesin = self._get_data_mesin()
		master_mesin = self.env['mrp.mesin'].search([('company_id','=',self.company_id.id)])
		row = 5
		first_col_total = 1
		last_col_total = first_col_total + 1
		# ========== BODY ==============
		# ========== Looping day in month ==============
		for month in range(self.start_date.month, self.end_date.month + 1):
			total_lwbp = 0
			total_bwp = 0
			total_kvarh = 0
			total_lwbp_bwp = 0
			total_kwh_terpakai = 0
			mapping_total_data_mesin = []
			for day in range(1,
							 monthrange(self.start_date.year, month)[1] + 1):
				worksheet.write(row, 1, MONTH[month - 1], header_table)
				worksheet.write(row, 2, str(day), header_table)
				worksheet.write(row, 3, '-', body_table)
				worksheet.write(row, 4, '-', body_table)
				worksheet.write(row, 5, '-', body_table)
				worksheet.write(row, 6, '-', body_table)
				worksheet.write(row, 7,'-', body_table)
				# ========== Looping KWH ==============
				for kwh in data_kwh:
					if kwh.get('date'):
						if kwh.get('date') == date(self.start_date.year, month,
												   day):
							worksheet.write(row, 3, kwh.get('lwbp') or '-', body_table_des)
							worksheet.write(row, 4, kwh.get('bwp') or '-', body_table_des)
							worksheet.write(row, 5, kwh.get('kvarh') or '-', body_table_des)
							worksheet.write(row, 6, kwh.get('lwbp_bwp') or '-', body_table_des)
							worksheet.write(
								row, 7,
								kwh.get('kwh_terpakai') * float(self.kwh_meter)
								or '-', body_table_des)
							total_lwbp = total_lwbp + kwh.get('lwbp')
							total_bwp = total_bwp + kwh.get('bwp')
							total_kvarh = total_kvarh + kwh.get('kvarh')
							total_lwbp_bwp = total_lwbp_bwp + kwh.get('lwbp_bwp')
							total_kwh_terpakai = total_kwh_terpakai + (kwh.get('kwh_terpakai') * float(self.kwh_meter))

				first_col = 8
				last_col = first_col + 2
				total_kwh_all = 0
				total_mesin_plastik = 0
				total_mesin_amdk = 0
				total_kwh_plastik = 0
				total_kwh_amdk = 0
				# ========== Looping data mesin ==============
				for master in master_mesin:
					worksheet.merge_range(3, first_col, 3, last_col,
												master.name, header_table)
					worksheet.write(4, first_col, 'Hasil Produksi', header_table)
					worksheet.write(4, first_col + 1, 'RH', header_table)
					worksheet.write(4, first_col + 2, 'KWh', header_table)
					worksheet.write(row, first_col, '-', body_table)
					worksheet.write(row, first_col+1, '-', body_table)
					worksheet.write(row, first_col+2, '-', body_table)
					total_production = 0
					total_rh = 0
					total_kwh = 0
					
					for mesin in data_mesin:
						if mesin.get('date_deadline'):
							if mesin.get('date_deadline') == date(self.start_date.year, month,
													day) and master.name == mesin.get('name'):
								worksheet.write(row, first_col, mesin.get('production') or '-', body_table)
								worksheet.write(row, first_col+1, mesin.get('rh') or '-', body_table)
								worksheet.write(row, first_col+2, mesin.get('kwh') or'-', body_table)
								total_production = total_production + mesin.get('production')
								total_rh = total_rh + mesin.get('rh')
								total_kwh = total_kwh + mesin.get('kwh')
								total_kwh_all += total_kwh

								if mesin.get('type_mesin') == 'AMDK':
									total_mesin_amdk += mesin.get('production')
									total_kwh_amdk += mesin.get('kwh')
								elif mesin.get('type_mesin') == 'PLASTIK':
									total_mesin_plastik += mesin.get('production')
									total_kwh_plastik += mesin.get('kwh')
								
					
					mapping_total_data_mesin.append({
									'name':master.name,
									'first_col':first_col})
					first_col = last_col + 1
					last_col = first_col + 2

				# ========== Calculate total per day ==============
				# ========== Header ==============
				last_col = last_col - 2
				worksheet.merge_range(3, last_col, 4, last_col,'Total Hasil Produksi Cup + Btl (karton)', header_table)
				worksheet.merge_range(3, last_col + 1, 4, last_col + 1,'Total Hasil Produksi Plastik Packaging (pcs)', header_table)
				worksheet.merge_range(3, last_col + 2, 4, last_col + 2,'Total KWH Standard Cup + Btl (karton)', header_table)
				worksheet.merge_range(3, last_col + 3, 4, last_col + 3,'Total KWH Standard Plastik Packaging (pcs)', header_table)
				worksheet.merge_range(3, last_col + 4, 4, last_col + 4,'Total KWH Standard Cup + Btl + Plastik Packaging', header_table)
				worksheet.merge_range(3, last_col + 5, 4, last_col + 5,'Selisih Kwh Terpakai dengan Kwh Standard', header_table)
				worksheet.merge_range(3, last_col + 6, 4, last_col + 6,'Harga per KWh Bulan Terakhir', header_table)
				worksheet.merge_range(3, last_col + 7, 4, last_col + 7,'Lost Vallue Kwh (Rp)', header_table)
				# ========== Detail ==============
				worksheet.write(row, last_col, total_mesin_amdk, body_table)
				worksheet.write(row, last_col + 1, total_mesin_plastik, body_table)
				worksheet.write(row, last_col + 2, total_kwh_amdk, body_table)
				worksheet.write(row, last_col + 3, total_kwh_plastik, body_table)
				worksheet.write(row, last_col + 4, total_kwh_all, body_table)
				worksheet.write(row, last_col + 5, (total_kwh_terpakai-total_kwh_all), body_table)
				worksheet.write(row, last_col + 6, self.kwh_price, body_table)
				worksheet.write(row, last_col + 7, (total_kwh_terpakai-total_kwh_all) * self.kwh_price, body_table)
				row = row + 1
			# ========== Calculate total per month ==============
			worksheet.merge_range(row, first_col_total, row, last_col_total,'Total', header_table)
			worksheet.write(row, 3, total_lwbp or '-', body_table)
			worksheet.write(row, 4, total_bwp or '-', body_table)
			worksheet.write(row, 5, total_kvarh or '-', body_table)
			worksheet.write(row, 6, total_lwbp_bwp or '-', body_table)
			worksheet.write(row, 7, total_kwh_terpakai or '-', body_table)
			# ========== Calculate total per month of day ==============
			worksheet.write(row, last_col, 0.0, body_table)
			worksheet.write(row, last_col + 1, 0.0, body_table)
			worksheet.write(row, last_col + 2, 0.0, body_table)
			worksheet.write(row, last_col + 3, 0.0, body_table)
			worksheet.write(row, last_col + 4, 0.0, body_table)
			worksheet.write(row, last_col + 5, 0.0, body_table)
			for mapping in mapping_total_data_mesin:
				total_data = self._calculate_total_per_mesin(month,mapping.get('name'))
				worksheet.write(row, int(mapping.get('first_col')), total_data.get('production') or'-', body_table)
				worksheet.write(row, int(mapping.get('first_col')) + 1, total_data.get('rh') or'-', body_table)
				worksheet.write(row, int(mapping.get('first_col')) + 2, total_data.get('kwh') or'-', body_table)
			row = row + 1
		
			worksheet.set_column(last_col,last_col+5, 25)

		workbook.close()
		out = base64.b64encode(fp.getvalue())
		fp.close()
		filename = ('energy_consumption_report.xlsx')
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