from odoo import api, fields, models, tools
import base64
from datetime import date
from io import BytesIO

try:
	from odoo.tools.misc import xlsxwriter
except ImportError:
	import xlsxwriter


class WizardReportTax05Report(models.TransientModel):
	_name = 'wizard.report.tax.05'
	_description = 'Wizard Report Tax 05'

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
		# ============versi no color============
		title = workbook.add_format({'bold': True, 'valign': 'bottom', 'align': 'center', 'text_wrap': True})
		title_no_bold = workbook.add_format({'bold': False, 'valign': 'vcenter', 'align': 'center', 'text_wrap': True})
		header_table = workbook.add_format({'valign': 'vcenter', 'align': 'center', 'text_wrap': True})
		left_bold = workbook.add_format({'bold': True, 'align': 'left', 'valign': 'vcenter', 'border': 1})
		left_no_bold = workbook.add_format({'bold': False, 'align': 'left', 'valign': 'vcenter', 'border': 1})
		center_bold = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1})
		center_no_bold = workbook.add_format({'bold': False, 'align': 'center', 'valign': 'vcenter', 'border': 1})
		right_no_bold = workbook.add_format({'bold': False, 'align': 'right', 'valign': 'vcenter', 'border': 1})
		right_bold = workbook.add_format({'bold': True, 'align': 'right', 'valign': 'vcenter', 'border': 1})
		# ============versi with color 1 #8DABDB============
		left_bold_8DABDB = workbook.add_format({'bold': True, 'align': 'left', 'valign': 'vcenter', 'border': 1,'bg_color':'#8DABDB'})
		left_no_bold_8DABDB = workbook.add_format({'bold': False, 'align': 'left', 'valign': 'vcenter', 'border': 1, 'bg_color':'#8DABDB'})
		center_bold_8DABDB = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1,'bg_color':'#8DABDB'})
		center_no_bold_8DABDB = workbook.add_format({'bold': False, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color':'#8DABDB'})
		right_no_bold_8DABDB = workbook.add_format({'bold': False, 'align': 'right', 'valign': 'vcenter', 'border': 1, 'bg_color':'#8DABDB'})
		right_bold_8DABDB = workbook.add_format({'bold': True, 'align': 'right', 'valign': 'vcenter', 'border': 1, 'bg_color':'#8DABDB'})
		# ============versi with color 2 #BFBFBF============
		left_bold_BFBFBF = workbook.add_format({'bold': True, 'align': 'left', 'valign': 'vcenter', 'border': 1, 'bg_color': '#BFBFBF'})
		left_no_bold_BFBFBF = workbook.add_format({'bold': False, 'align': 'left', 'valign': 'vcenter', 'border': 1, 'bg_color': '#BFBFBF'})
		center_bold_BFBFBF = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#BFBFBF'})
		center_no_bold_BFBFBF = workbook.add_format({'bold': False, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#BFBFBF'})
		right_no_bold_BFBFBF = workbook.add_format({'bold': False, 'align': 'right', 'valign': 'vcenter', 'border': 1, 'bg_color': '#BFBFBF'})
		right_bold_BFBFBF = workbook.add_format({'bold': True, 'align': 'right', 'valign': 'vcenter', 'border': 1, 'bg_color': '#BFBFBF'})
		# ============versi with color 3 #2D75B5 font white============
		left_bold_2D75B5_white = workbook.add_format({'bold': True, 'align': 'left', 'valign': 'vcenter', 'border': 1, 'bg_color': '#2D75B5','font_color': 'white'})
		left_no_bold_2D75B5_white = workbook.add_format({'bold': False, 'align': 'left', 'valign': 'vcenter', 'border': 1, 'bg_color': '#2D75B5','font_color': 'white'})
		center_bold_2D75B5_white = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#2D75B5','font_color': 'white'})
		center_no_bold_2D75B5_white = workbook.add_format({'bold': False, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#2D75B5','font_color': 'white'})
		right_no_bold_2D75B5_white = workbook.add_format({'bold': False, 'align': 'right', 'valign': 'vcenter', 'border': 1, 'bg_color': '#2D75B5','font_color': 'white'})
		right_bold_2D75B5_white = workbook.add_format({'bold': True, 'align': 'right', 'valign': 'vcenter', 'border': 1, 'bg_color': '#2D75B5','font_color': 'white'})
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
		worksheet.merge_range('G1:L1', 'PILIHAN (OPSI) DAPAT DILIHAT PADA LIST KODE BARANG YG MANA MASUK BAHAN BAKU, BARANG JADI, ASET, SPAREPART, BIAYA, DLL)',title)
		worksheet.merge_range('A2:A4', 'MASA', center_bold_8DABDB)
		worksheet.merge_range('B2:B4', 'KODE SUPPLIER', center_bold_8DABDB)
		worksheet.merge_range('C2:C4', 'NAMA KONSUMEN/SUPPLIER (PT, CV, ORANG PRIBADI)', center_bold_8DABDB)
		worksheet.merge_range('D2:D4', 'ALAMAT', center_bold_8DABDB)
		worksheet.merge_range('E2:E4', 'NPWP', center_bold_8DABDB)
		worksheet.merge_range('F2:F4', 'NIK', center_bold_8DABDB)

		worksheet.merge_range('G2:L3','JENIS TRANSAKSI',center_bold_BFBFBF)
		worksheet.write('G4', 'BAHAN BAKU', center_bold_BFBFBF)
		worksheet.write('H4', 'BARANG JADI', center_bold_BFBFBF)
		worksheet.write('I4', 'ASSET', center_bold_BFBFBF)
		worksheet.write('J4', 'SPAREPART', center_bold_BFBFBF)
		worksheet.write('K4', 'BIAYA', center_bold_BFBFBF)
		worksheet.write('L4', 'LAIN LAIN', center_bold_BFBFBF)

		worksheet.merge_range('M2:M4', 'TANGGAL INVOICE/PO', center_bold_8DABDB)
		worksheet.merge_range('N2:N4', 'NOMOR INVOICE/PO/RETUR', center_bold_8DABDB)
		worksheet.merge_range('O2:O4', 'NOMOR FAKTUR PAJAK', center_bold_8DABDB)

		worksheet.merge_range('P2:AA2', 'SYSTEM ACCOUNTING', center_bold_2D75B5_white)
		worksheet.merge_range('P3:AA3', 'PEMBELIAN', center_bold_2D75B5_white)
		worksheet.write('P4', 'JURNAL NO', center_bold_2D75B5_white)
		worksheet.write('Q4', 'KODE BARANG', center_bold_2D75B5_white)
		worksheet.write('R4', 'QTY', center_bold_2D75B5_white)
		worksheet.write('S4', 'HARGA', center_bold_2D75B5_white)
		worksheet.write('T4', 'TOTAL', center_bold_2D75B5_white)
		worksheet.write('U4', 'Dasar Penegenaan Pajak', center_bold_2D75B5_white)
		worksheet.write('V4', 'PPN', center_bold_2D75B5_white)
		worksheet.write('W4', 'PPH 21', center_bold_2D75B5_white)
		worksheet.write('X4', 'PPH 22', center_bold_2D75B5_white)
		worksheet.write('Y4', 'PPH 23', center_bold_2D75B5_white)
		worksheet.write('Z4', 'PPH 26', center_bold_2D75B5_white)
		worksheet.write('AA4', 'PPH 4(2)', center_bold_2D75B5_white)
		worksheet.merge_range('AB2:AB4', 'KET.', center_bold_2D75B5_white)

		worksheet.merge_range('AC2:AE3', 'RETUR', center_bold_8DABDB)
		worksheet.write('AC4', 'QTY', center_bold_8DABDB)
		worksheet.write('AD4', 'HARGA', center_bold_8DABDB)
		worksheet.write('AE4', 'JUMLAH', center_bold_8DABDB)

		worksheet.merge_range('AF2:AF4', 'TOTAL JUMLAH (NET)', center_bold_2D75B5_white)
		worksheet.merge_range('AG2:AN3', '', center_bold_2D75B5_white)
		worksheet.write('AG4', 'Dasar Penegenaan Pajak', center_bold_2D75B5_white)
		worksheet.write('AH4', 'PPN', center_bold_2D75B5_white)
		worksheet.write('AI4', 'PPH 21', center_bold_2D75B5_white)
		worksheet.write('AJ4', 'PPH 22', center_bold_2D75B5_white)
		worksheet.write('AK4', 'PPH 23', center_bold_2D75B5_white)
		worksheet.write('AL4', 'PPH 25', center_bold_2D75B5_white)
		worksheet.write('AM4', 'PPH 26', center_bold_2D75B5_white)
		worksheet.write('AN4', 'PPH 4(2)', center_bold_2D75B5_white)
		worksheet.merge_range('AO2:AO4', 'TANGGAL BAYAR SETORAN PAJAK', center_bold_2D75B5_white)
		worksheet.merge_range('AP2:AP4', 'TANGGAL LAPOR PAJAK', center_bold_2D75B5_white)

		worksheet.merge_range('AR2:AU2', 'JUMLAH', center_bold)
		worksheet.merge_range('AR3:AS3', 'PIUTANG', center_bold)
		worksheet.merge_range('AT3:AU3', 'HUTANG', center_bold)
		worksheet.write('AR4', 'SALDO AWAL', center_bold)
		worksheet.write('AS4', 'TOTAL PIUTANG', center_bold)
		worksheet.write('AT4', 'SALDO AWAL', center_bold)
		worksheet.write('AU4', 'TOTAL HUTANG', center_bold)
		worksheet.merge_range('AV2:AX3', 'KAS/BANK', center_bold)
		worksheet.write('AV4', 'TANGGAL PEMBAYARAN', center_bold)
		worksheet.write('AW4', 'JUMLAH PEMBAYARAN', center_bold)
		worksheet.write('AX4', 'DESKRIPSI/KET', center_bold)
		worksheet.merge_range('AY2:AZ3', 'SISA OUTSTANDING', center_bold)
		worksheet.write('AY4', 'JUMLAH PEMBAYARAN', center_bold)
		worksheet.write('AZ4', 'DESKRIPSI/KET', center_bold)

		worksheet.write('AS4', 'Total per GL', center_bold)
		worksheet.write('AT4', 'Total per FP', center_bold)
		worksheet.write('AU4', 'Perbedaan', center_bold)

		workbook.close()
		out = base64.b64encode(fp.getvalue())
		fp.close()
		filename = ('LIST_KODE_BARANG.xlsx')
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