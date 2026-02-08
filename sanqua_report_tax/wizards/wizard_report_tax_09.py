from odoo import api, fields, models, tools
import logging
_logger = logging.getLogger(__name__)
import base64
from datetime import date
from io import BytesIO

try:
	from odoo.tools.misc import xlsxwriter
except ImportError:
	import xlsxwriter


class WizardReportTax09Report(models.TransientModel):
	_name = 'wizard.report.tax.09'
	_description = 'Wizard Report Tax 09'

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
		
		header_table = workbook.add_format({'bold': True,'align':'left','text_wrap':True})
		header_table.set_border(2)
		header_section = workbook.add_format({'bold': True,'align':'left','text_wrap':True})
		header_section.set_border(2)

		worksheet.set_column('B:D', 20)
		worksheet.set_column('E:E', 25)
		worksheet.set_column('F:F', 15)
		worksheet.set_column('G:H', 20)
		worksheet.set_column('I:K', 25)

		# ========== HEADER STATIS ==============
		worksheet.merge_range('B1:K1', 'IDENTIFIKASI KEWAJIBAN WITHOLDING TAX PT. ', title)
		worksheet.merge_range('B2:K2', 'TAHUN ', title)
		worksheet.merge_range('B3:K3', 'REKAPAN')
		worksheet.merge_range('B4:K4', 'PASAL 23',header_section)
		worksheet.merge_range('B5:K5', '',header_section)
		worksheet.write('B6', 'MASA', header_table)
		worksheet.write('C6', 'NAMA', header_table)
		worksheet.write('D6', 'NPWP', header_table)
		worksheet.write('E6', 'Jenis Transaksi', header_table)
		worksheet.write('F6', 'KJS/KAP', header_table)
		worksheet.write('G6', 'TGL BAYAR', header_table)
		worksheet.write('H6', 'TGL LAPOR', header_table)
		worksheet.write('I6', 'JUMLAH PH BRUTO', header_table)
		worksheet.write('J6', 'PPH TERUTANG', header_table)
		worksheet.write('K6', 'KETERANGAN', header_table)

		workbook.close()
		out = base64.b64encode(fp.getvalue())
		fp.close()
		filename = ('Identifikasi_Kewajiban.xlsx')
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