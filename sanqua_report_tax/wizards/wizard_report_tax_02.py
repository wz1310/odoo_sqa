from odoo import api, fields, models, tools
import base64
from datetime import date
from io import BytesIO

try:
	from odoo.tools.misc import xlsxwriter
except ImportError:
	import xlsxwriter


class WizardReportTax02Report(models.TransientModel):
	_name = 'wizard.report.tax.02'
	_description = 'Wizard Report Tax 02'

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
		# title = workbook.add_format({'bold': True,'valign':'vcenter','align':'center','text_wrap':True})
		# header_table = workbook.add_format({'valign':'vcenter','align':'center','text_wrap':True})
		title = workbook.add_format({'bold': True, 'valign': 'bottom', 'align': 'center', 'text_wrap': True})
		title_no_bold = workbook.add_format({'bold': False, 'valign': 'vcenter', 'align': 'center', 'text_wrap': True})
		header_table = workbook.add_format({'valign': 'vcenter', 'align': 'center', 'text_wrap': True})
		left_bold = workbook.add_format({'bold': True, 'align': 'left', 'valign': 'vcenter', 'border': 1})
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
		worksheet.merge_range('B2:N2', 'KERTAS KERJA EKUALISASI BIAYA DAN OBJEK PPH POTONG PUNGUT (POTPUT)',title)
		worksheet.merge_range('B3:N3', 'EKUALISASI PPH PASAL 21', title)
		worksheet.merge_range('B5:M5', 'Biaya Gaji dll cfm SPT TAHUNAN PPH BADAN', left_bold)
		worksheet.merge_range('B6:N6', 'Penghasilan Bruto cfm SPT Masa PPH Pasal 21/26', left_no_bold)
		worksheet.merge_range('B7:L7', 'Januari', right_no_bold)
		worksheet.merge_range('B8:L8', 'Februari', right_no_bold)
		worksheet.merge_range('B9:L9', 'Maret', right_no_bold)
		worksheet.merge_range('B10:L10', 'April', right_no_bold)
		worksheet.merge_range('B11:L11', 'Mei', right_no_bold)
		worksheet.merge_range('B12:L12', 'Juni', right_no_bold)
		worksheet.merge_range('B13:L13', 'Juli', right_no_bold)
		worksheet.merge_range('B14:L14', 'Agustus', right_no_bold)
		worksheet.merge_range('B15:L15', 'September', right_no_bold)
		worksheet.merge_range('B16:L16', 'Oktober', right_no_bold)
		worksheet.merge_range('B17:L17', 'November', right_no_bold)
		worksheet.merge_range('B18:L18', 'Desember', right_no_bold)
		worksheet.merge_range('B19:L19', 'Total Penghasilan Bruto', right_bold)
		worksheet.merge_range('B20:L20', 'Selisih', left_bold)
		worksheet.merge_range('B21:L21', 'Natura, Kenikmatan', right_no_bold)
		worksheet.merge_range('B22:L22', 'JHT', right_no_bold)
		worksheet.merge_range('B23:L23', 'Perbedaan Tahun Pengakuan Biaya dan Pemotongan', right_no_bold)
		worksheet.merge_range('B24:L24', 'Selisih Kurs', right_no_bold)
		worksheet.merge_range('B25:L25', 'Total', right_bold)

		worksheet.write('M7', 'Rp-   ', left_no_bold)
		worksheet.write('M8', 'Rp-   ', left_no_bold)
		worksheet.write('M9', 'Rp-   ', left_no_bold)
		worksheet.write('M10', 'Rp-   ', left_no_bold)
		worksheet.write('M11', 'Rp-   ', left_no_bold)
		worksheet.write('M12', 'Rp-   ', left_no_bold)
		worksheet.write('M13', 'Rp-   ', left_no_bold)
		worksheet.write('M14', 'Rp-   ', left_no_bold)
		worksheet.write('M15', 'Rp-   ', left_no_bold)
		worksheet.write('M16', 'Rp-   ', left_no_bold)
		worksheet.write('M17', 'Rp-   ', left_no_bold)
		worksheet.write('M18', 'Rp-   ', left_no_bold)
		worksheet.write('M19', '   ', left_no_bold)
		worksheet.write('M20', '   ', left_no_bold)
		worksheet.write('M21', 'Rp-   ', left_no_bold)
		worksheet.write('M22', 'Rp-   ', left_no_bold)
		worksheet.write('M23', '   ', left_no_bold)
		worksheet.write('M24', 'Rp-   ', left_no_bold)
		worksheet.write('M25', '   ', left_no_bold)

		worksheet.write('N5', 'Rp-   ', left_bold)
		worksheet.write('N7', '   ', left_no_bold)
		worksheet.write('N8', '   ', left_no_bold)
		worksheet.write('N9', '   ', left_no_bold)
		worksheet.write('N10', '   ', left_no_bold)
		worksheet.write('N11', '   ', left_no_bold)
		worksheet.write('N12', '   ', left_no_bold)
		worksheet.write('N13', '   ', left_no_bold)
		worksheet.write('N14', '   ', left_no_bold)
		worksheet.write('N15', '   ', left_no_bold)
		worksheet.write('N16', '   ', left_no_bold)
		worksheet.write('N17', '   ', left_no_bold)
		worksheet.write('N18', '   ', left_no_bold)
		worksheet.write('N19', 'Rp-   ', left_bold)
		worksheet.write('N20', 'Rp-   ', left_bold)
		worksheet.write('N21', '   ', left_no_bold)
		worksheet.write('N22', '   ', left_no_bold)
		worksheet.write('N23', '   ', left_no_bold)
		worksheet.write('N24', '   ', left_no_bold)
		worksheet.write('N25', 'RP-   ', left_bold)

		workbook.close()
		out = base64.b64encode(fp.getvalue())
		fp.close()
		filename = ('EKUALISASI_BIAYA_DAN_OBJEK_PPH_POTONG_PUNGUT.xlsx')
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