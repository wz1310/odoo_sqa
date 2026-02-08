from odoo import api, fields, models, tools
import base64
from datetime import date
from io import BytesIO

try:
	from odoo.tools.misc import xlsxwriter
except ImportError:
	import xlsxwriter


class WizardReportTax01Report(models.TransientModel):
	_name = 'wizard.report.tax.01'
	_description = 'Wizard Report Tax 01'

	YEARS = [(str(num), str(num))
			 for num in range(2010, (date.today().year) + 1)]

	year = fields.Selection(YEARS, string='Period', required=True)
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
		title = workbook.add_format({'bold': True,'valign':'bottom','align':'center','text_wrap':True})
		title_no_bold = workbook.add_format({'bold': False, 'valign': 'vcenter', 'align': 'center', 'text_wrap': True})
		header_table = workbook.add_format({'valign':'vcenter','align':'center','text_wrap':True})
		left_bold = workbook.add_format({'bold': True,'align': 'left','valign':'vcenter', 'border': 1})
		left_no_bold = workbook.add_format({'bold': False, 'align': 'left', 'valign': 'vcenter', 'border': 1})
		right_no_bold = workbook.add_format({'bold': False, 'align': 'right', 'valign': 'vcenter', 'border': 1})
		right_bold = workbook.add_format({'bold': True, 'align': 'right', 'valign': 'vcenter', 'border': 1})
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
		worksheet.merge_range('B1:N1', 'PILIHAN (OPSI) DAPAT DILIHAT PADA LIST KODE BARANG YG MANA MASUK BAHAN BAKU, BARANG JADI, ASET, SPAREPART, BIAYA, DLL)', title_no_bold)
		worksheet.merge_range('B2:N4', 'KERTAS KERJA EKUALISASI PENGHASILAN DAN OBJEK PPN',title)
		worksheet.merge_range('B5:L5', 'Penghasilan cfm. SPT TAHUNAN BADAN', left_bold)
		worksheet.write('M5', '', header_table)
		worksheet.write('N5', 'Rp-   ', header_table)
		worksheet.merge_range('B6:N6', 'Penyerahan Lokal & Ekspor cfm SPT Masa PPN', left_no_bold)
		worksheet.merge_range('B7:L7', 'Januari - Desember', right_no_bold)
		worksheet.merge_range('B8:L8', 'Total Penyerahan', right_no_bold)
		worksheet.merge_range('B9:L9', 'Selisih', left_bold)
		worksheet.merge_range('B10:L10', 'Bukan Objek PPN', right_no_bold)
		worksheet.merge_range('B11:L11', 'Penyerahan antar cabang, Pemakaian sendiri, Pemberian Cuma Cuma, Pengalihan Aktiva', right_no_bold)
		worksheet.merge_range('B12:L12', 'Penjualan Tahun Lalu; FP Tahun ini', right_no_bold)
		worksheet.merge_range('B13:L13', 'Penjualan Tahun ini; FP Tahun berikutnya', right_no_bold)
		worksheet.merge_range('B14:L14', 'Selisih Kurs', right_no_bold)
		worksheet.merge_range('B15:L15', 'Pengembalian Tahun lalu; NR Tahun ini', right_no_bold)
		worksheet.merge_range('B16:L16', 'Pengembalian Tahun lalu; NR Tahun ini', right_no_bold)
		worksheet.merge_range('B17:L17', 'Pembayaran Uang Muka', right_no_bold)
		worksheet.merge_range('B18:L18', 'Total', right_bold)

		worksheet.write('M5', '   ', left_no_bold)
		worksheet.write('M7', 'Rp-   ', left_no_bold)
		worksheet.write('M8', '   ', left_no_bold)
		worksheet.write('M9', '   ', left_no_bold)
		worksheet.write('M10', 'Rp-   ', left_no_bold)
		worksheet.write('M11', 'Rp-   ', left_no_bold)
		worksheet.write('M12', 'Rp-   ', left_no_bold)
		worksheet.write('M13', 'Rp-   ', left_no_bold)
		worksheet.write('M14', 'Rp-   ', left_no_bold)
		worksheet.write('M15', 'Rp-   ', left_no_bold)
		worksheet.write('M16', 'Rp-   ', left_no_bold)
		worksheet.write('M17', '   ', left_no_bold)
		worksheet.write('M18', '   ', left_no_bold)

		worksheet.write('N5', 'Rp-   ', left_bold)
		worksheet.write('N7', '   ', left_no_bold)
		worksheet.write('N8', 'Rp-   ', left_no_bold)
		worksheet.write('N9', 'Rp-   ', left_bold)
		worksheet.write('N10', '   ', left_no_bold)
		worksheet.write('N11', '   ', left_no_bold)
		worksheet.write('N12', '   ', left_no_bold)
		worksheet.write('N13', '   ', left_no_bold)
		worksheet.write('N14', '   ', left_no_bold)
		worksheet.write('N15', '   ', left_no_bold)
		worksheet.write('N16', '   ', left_no_bold)
		worksheet.write('N17', 'Rp-   ', left_no_bold)
		worksheet.write('N18', 'Rp-   ', left_bold)


		workbook.close()
		out = base64.b64encode(fp.getvalue())
		fp.close()
		filename = ('EKUALISASI_PENGHASILAN_DAN_OBJEK_PPN.xlsx')
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