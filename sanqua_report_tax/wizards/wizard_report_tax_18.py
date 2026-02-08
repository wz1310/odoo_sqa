from odoo import api, fields, models, tools
import base64
from datetime import date
from io import BytesIO

try:
	from odoo.tools.misc import xlsxwriter
except ImportError:
	import xlsxwriter


class WizardReportTax18Report(models.TransientModel):
	_name = 'wizard.report.tax.18'
	_description = 'Wizard Report Tax 18'

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
		header_table.set_border(2)
		left_table = workbook.add_format({'align':'left','text_wrap':True})
		left_table.set_border(2)

		# worksheet.set_column('A:O', 27)
		worksheet.set_column('A:C', 20)
		worksheet.set_column('I:J', 25)
		worksheet.set_column('H:H', 20)
		worksheet.set_column('D:F', 32)
		worksheet.set_column('K:M', 32)
		worksheet.set_column('G:G', 40)
		worksheet.set_column('N:N', 40)
		worksheet.set_column('O:O', 20)

		# ========== HEADER STATIS ==============
		worksheet.merge_range('A1:O1', 'IDENTIFIKASI KEWAJIBAN WITHOLDING TAX PT. ', title)
		worksheet.merge_range('A2:O2', 'TAHUN. ', title)
		worksheet.merge_range('A4:A5', self.year + '\n MASA', header_table)
		worksheet.merge_range('B4:G4', 'PASAL 21				GL', left_table)
		worksheet.write('B5', 'TGL BAYAR', header_table)
		worksheet.write('C5', 'BUKTI JURNAL', header_table)
		worksheet.write('D5', 'KODE OBJEK PAJAK', header_table)
		worksheet.write('E5', 'JUMLAH PENERIMA PH (ORANG)', header_table)
		worksheet.write('F5', 'JUMLAH PH BRUTO', header_table)
		worksheet.write('G5', 'JUMLAH PPH TERHUTANG DI GL BIAYA PPH 21', header_table)
		worksheet.merge_range('H4:H5', 'KET', header_table)
		worksheet.merge_range('I4:O4', 'ESPT', left_table)
		worksheet.write('I5', 'TANGGAL BAYAR', header_table)
		worksheet.write('J5', 'TANGGAL LAPOR', header_table)
		worksheet.write('K5', 'KODE OBJEK PAJAK', header_table)
		worksheet.write('L5', 'JUMLAH PENERIMA PH (ORANG)', header_table)
		worksheet.write('M5', 'JUMLAH PH BRUTO', header_table)
		worksheet.write('N5', 'JUMLAH PPH TERHUTANG DI GL BIAYA PPH 21', header_table)
		worksheet.write('O5', 'KETERANGAN', header_table)
		
		workbook.close()
		out = base64.b64encode(fp.getvalue())
		fp.close()
		filename = ('IDENTIFIKASI_KEWAJIBAN.xlsx')
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