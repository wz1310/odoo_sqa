from odoo import api, fields, models, tools
import base64
from datetime import date
from io import BytesIO

try:
	from odoo.tools.misc import xlsxwriter
except ImportError:
	import xlsxwriter


class WizardReportTax07Report(models.TransientModel):
	_name = 'wizard.report.tax.07'
	_description = 'Wizard Report Tax 07'

	YEARS = [(str(num), str(num))
			 for num in range(2010, (date.today().year) + 1)]

	year = fields.Selection(YEARS, string='Year', required=True)
	name = fields.Char(string="Filename", readonly=True)
	data_file = fields.Binary(string="File", readonly=True)

	def button_print(self):
		data = []
		return self.generate_excel(data)

	def generate_excel(self, data):
		""" Generate excel based from label.print record. """
		fp = BytesIO()
		workbook = xlsxwriter.Workbook(fp)
		worksheet = workbook.add_worksheet()
		
		# ========== Format ==============
		title = workbook.add_format({'bold': True,'valign':'vcenter','align':'center','text_wrap':True})
		header_table = workbook.add_format({'valign':'vcenter','align':'center','text_wrap':True})
		header_table.set_border()

		body_table = workbook.add_format()
		body_table.set_align('right')
		body_table.set_align('vcenter')
		body_table.set_border(1)
		body_table.set_num_format('#,##0')

		worksheet.set_column('B:P', 23)
		worksheet.set_column('Q:S', 30)
		# worksheet.set_column('G:H', 30)

		# ========== HEADER STATIS ==============
		worksheet.merge_range('A3:T3', 'EKUALISASI PPN : ANTARA BB (LEDGER) ATAU SPT TH PPH BADAN :',title)
		worksheet.merge_range('A5:A6', self.year + '\n MASA', header_table)
		worksheet.merge_range('B5:B6', 'TANGGAL LAPOR', header_table)
		worksheet.merge_range('C5:C6', 'TANGGAL BAYAR', header_table)
		worksheet.merge_range('D5:E6', 'LEDGER / SPT Th PPh Badan (Accurate)', header_table)
		worksheet.write('D6', 'Penjualan', header_table)
		worksheet.write('E6', 'Pembelian', header_table)
		worksheet.write('F5', '', header_table)
		worksheet.write('F6', 'Penjualan - Pembelian', header_table)
		worksheet.write('G5', '', header_table)
		worksheet.write('G6', 'LB SEBELUMNYA ***', header_table)
		worksheet.write('H5', '', header_table)
		worksheet.write('H6', 'PM ***', header_table)
		worksheet.write('I5', '', header_table)
		worksheet.write('I6', 'JUMLAH PPH TERHUTANG', header_table)
		worksheet.merge_range('J5:Q5', 'SPT MASA PPN', header_table)
		worksheet.write('J6', 'PK', header_table)
		worksheet.write('K6', 'PM', header_table)
		worksheet.write('L6', 'PK-PM (PPn Terhutang)', header_table)
		worksheet.write('M6', 'LB SEBELUMNYA', header_table)
		worksheet.write('N6', 'PM ***', header_table)
		worksheet.write('O6', 'JUMLAH PPN TERHUTANG', header_table)
		worksheet.write('P6', 'DIBAYAR', header_table)
		worksheet.write('Q6', 'PPN PADA SPT PEMBETULAN', header_table)
		worksheet.merge_range('R5:R6', 'Menurut Ledger PK - PM', header_table)
		worksheet.merge_range('S5:S6', 'Beda SPT Masa PPN - Ledger', header_table)
		worksheet.merge_range('T5:T6', 'KET.', header_table)

		workbook.close()
		out = base64.b64encode(fp.getvalue())
		fp.close()
		filename = ('Ekualisasi_PPN.xlsx')
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