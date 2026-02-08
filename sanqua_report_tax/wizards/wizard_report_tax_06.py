from odoo import api, fields, models, tools
import base64
from datetime import date
from io import BytesIO

try:
	from odoo.tools.misc import xlsxwriter
except ImportError:
	import xlsxwriter


class WizardReportTax06Report(models.TransientModel):
	_name = 'wizard.report.tax.06'
	_description = 'Wizard Report Tax 06'

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
		# ============versi with color 1 #7F7F7F============
		left_bold_7F7F7F = workbook.add_format(
			{'bold': True, 'align': 'left', 'valign': 'vcenter', 'border': 1, 'bg_color': '#7F7F7F'})
		left_no_bold_7F7F7F = workbook.add_format(
			{'bold': False, 'align': 'left', 'valign': 'vcenter', 'border': 1, 'bg_color': '#7F7F7F'})
		center_bold_7F7F7F = workbook.add_format(
			{'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#7F7F7F'})
		center_no_bold_7F7F7F = workbook.add_format(
			{'bold': False, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#7F7F7F'})
		right_no_bold_7F7F7F = workbook.add_format(
			{'bold': False, 'align': 'right', 'valign': 'vcenter', 'border': 1, 'bg_color': '#7F7F7F'})
		right_bold_7F7F7F = workbook.add_format(
			{'bold': True, 'align': 'right', 'valign': 'vcenter', 'border': 1, 'bg_color': '#7F7F7F'})
		# ============versi with color 2 #2D75B5 font white============
		left_bold_2D75B5_white = workbook.add_format(
			{'bold': True, 'align': 'left', 'valign': 'vcenter', 'border': 1, 'bg_color': '#2D75B5',
			 'font_color': 'white'})
		left_no_bold_2D75B5_white = workbook.add_format(
			{'bold': False, 'align': 'left', 'valign': 'vcenter', 'border': 1, 'bg_color': '#ç',
			 'font_color': 'white'})
		center_bold_2D75B5_white = workbook.add_format(
			{'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#2D75B5',
			 'font_color': 'white'})
		center_no_bold_2D75B5_white = workbook.add_format(
			{'bold': False, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#2D75B5',
			 'font_color': 'white'})
		right_no_bold_2D75B5_white = workbook.add_format(
			{'bold': False, 'align': 'right', 'valign': 'vcenter', 'border': 1, 'bg_color': '#2D75B5',
			 'font_color': 'white'})
		right_bold_2D75B5_white = workbook.add_format(
			{'bold': True, 'align': 'right', 'valign': 'vcenter', 'border': 1, 'bg_color': '#2D75B5',
			 'font_color': 'white'})
		# ============versi with color 3 #4372C4 font white============
		left_bold_4372C4_white = workbook.add_format(
			{'bold': True, 'align': 'left', 'valign': 'vcenter', 'border': 1, 'bg_color': '#4372C4',
			 'font_color': 'white'})
		left_no_bold_4372C4_white = workbook.add_format(
			{'bold': False, 'align': 'left', 'valign': 'vcenter', 'border': 1, 'bg_color': '#4372C4',
			 'font_color': 'white'})
		center_bold_4372C4_white = workbook.add_format(
			{'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#4372C4',
			 'font_color': 'white'})
		center_no_bold_4372C4_white = workbook.add_format(
			{'bold': False, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#4372C4',
			 'font_color': 'white'})
		right_no_bold_4372C4_white = workbook.add_format(
			{'bold': False, 'align': 'right', 'valign': 'vcenter', 'border': 1, 'bg_color': '#4372C4',
			 'font_color': 'white'})
		right_bold_4372C4_white = workbook.add_format(
			{'bold': True, 'align': 'right', 'valign': 'vcenter', 'border': 1, 'bg_color': '#4372C4',
			 'font_color': 'white'})
		# ============versi with color 4 yellow font black============
		left_bold_yellow_black = workbook.add_format(
			{'bold': True, 'align': 'left', 'valign': 'vcenter', 'border': 1, 'bg_color': 'yellow',
			 'font_color': 'black'})
		left_no_bold_yellow_black = workbook.add_format(
			{'bold': False, 'align': 'left', 'valign': 'vcenter', 'border': 1, 'bg_color': 'yellow',
			 'font_color': 'black'})
		center_bold_yellow_black = workbook.add_format(
			{'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': 'yellow',
			 'font_color': 'black'})
		center_no_bold_yellow_black = workbook.add_format(
			{'bold': False, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': 'yellow',
			 'font_color': 'black'})
		right_no_bold_yellow_black = workbook.add_format(
			{'bold': False, 'align': 'right', 'valign': 'vcenter', 'border': 1, 'bg_color': 'yellow',
			 'font_color': 'black'})
		right_bold_yellow_black = workbook.add_format(
			{'bold': True, 'align': 'right', 'valign': 'vcenter', 'border': 1, 'bg_color': 'yellow',
			 'font_color': 'black'})
		# ============versi with color 5 #5B9BD5 font black============
		left_bold_5B9BD5_black = workbook.add_format(
			{'bold': True, 'align': 'left', 'valign': 'vcenter', 'border': 1, 'bg_color': '#5B9BD5',
			 'font_color': 'black'})
		left_no_bold_5B9BD5_black = workbook.add_format(
			{'bold': False, 'align': 'left', 'valign': 'vcenter', 'border': 1, 'bg_color': '#5B9BD5',
			 'font_color': 'black'})
		center_bold_5B9BD5_black = workbook.add_format(
			{'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#5B9BD5',
			 'font_color': 'black'})
		center_no_bold_5B9BD5_black = workbook.add_format(
			{'bold': False, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#5B9BD5',
			 'font_color': 'black'})
		right_no_bold_5B9BD5_black = workbook.add_format(
			{'bold': False, 'align': 'right', 'valign': 'vcenter', 'border': 1, 'bg_color': '#5B9BD5',
			 'font_color': 'black'})
		right_bold_5B9BD5_black = workbook.add_format(
			{'bold': True, 'align': 'right', 'valign': 'vcenter', 'border': 1, 'bg_color': '#5B9BD5',
			 'font_color': 'black'})
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
		worksheet.write('B1', 'PENJUALAN',title_no_bold)
		worksheet.merge_range('H2:J2', 'NAMA KONSUMEN/SUPPLIER (PT, CV, ORANG PRIBADI)', center_no_bold)
		worksheet.merge_range('P1:AA1', 'PILIHAN (OPSI) DAPAT DILIHAT PADA LIST KODE BARANG YG MANA MASUK BAHAN BAKU, BARANG JADI, ASET, SPAREPART, BIAYA, DLL)', center_no_bold)

		worksheet.merge_range('B3:B5', 'NO', center_bold_7F7F7F)
		worksheet.merge_range('C3:C5', 'MASA', center_bold_7F7F7F)
		worksheet.merge_range('D3:D5', 'ID CUSTOMER', center_bold_7F7F7F)
		worksheet.merge_range('E3:E5', 'NIK', center_bold_7F7F7F)
		worksheet.merge_range('F3:F5', 'NPWP', center_bold_7F7F7F)
		worksheet.merge_range('G3:G5', 'NOMOR FAKTUR PAJAK', center_bold_7F7F7F)
		worksheet.merge_range('H3:H5', 'ALAMAT', center_bold_7F7F7F)
		worksheet.merge_range('I3:I5', 'NAMA CUSTOMER', center_bold_7F7F7F)

		worksheet.merge_range('J3:AA3', 'SYSTEM ACCOUNTING', center_bold_4372C4_white)

		worksheet.merge_range('J4:J5', 'NO INVOICE/NO PO', center_bold_4372C4_white)
		worksheet.merge_range('K4:K5', 'TGL INVOICE/NO PO', center_bold_4372C4_white)
		worksheet.merge_range('L4:L5', 'KODE BARANG', center_bold_4372C4_white)
		worksheet.merge_range('M4:M5', 'JENIS BARANG', center_bold_4372C4_white)
		worksheet.merge_range('N4:N5', 'QUANTITY', center_bold_4372C4_white)
		worksheet.merge_range('O4:O5', 'HARGA (exclude PPN)', center_bold_4372C4_white)
		worksheet.merge_range('P4:P5', 'TOTAL PENJUALAN (DASAR PENGENAAN PAJAK)', center_bold_4372C4_white)
		worksheet.merge_range('Q4:Q5', ' PPN 10% DARI DPP', center_bold_2D75B5_white)

		worksheet.merge_range('R4:R5', 'PPH 21', center_bold_2D75B5_white)
		worksheet.merge_range('S4:S5', 'PPH 22', center_bold_2D75B5_white)
		worksheet.merge_range('T4:T5', 'PPH 23', center_bold_2D75B5_white)
		worksheet.merge_range('U4:U5', 'PPH 26', center_bold_2D75B5_white)
		worksheet.merge_range('V4:V5', 'PPH 4(2)', center_bold_2D75B5_white)
		worksheet.merge_range('W4:Z4', 'RETUR', center_bold_4372C4_white)
		worksheet.write('W5', 'NOTA RETUR NO', center_bold_4372C4_white)
		worksheet.write('X5', 'QTY', center_bold_4372C4_white)
		worksheet.write('Y5', 'HARTA', center_bold_4372C4_white)
		worksheet.write('Z5', 'TOTAL', center_bold_4372C4_white)
		worksheet.merge_range('AA4:AA5', 'PENJUALAN BERSIH (NET)', center_bold_4372C4_white)

		worksheet.merge_range('AB3:AK3', '', center_bold_5B9BD5_black)
		worksheet.merge_range('AB4:AB5', 'DPP PPN', center_bold_5B9BD5_black)
		worksheet.merge_range('AC4:AC5', 'PPN 10 %', center_bold_5B9BD5_black)
		worksheet.merge_range('AD4:AD5', 'PPH 21', center_bold_2D75B5_white)
		worksheet.merge_range('AE4:AE5', 'PPH 22', center_bold_2D75B5_white)
		worksheet.merge_range('AF4:AF5', 'PPH 23', center_bold_2D75B5_white)
		worksheet.merge_range('AG4:AG5', 'PPH 25', center_bold_2D75B5_white)
		worksheet.merge_range('AH4:AH5', 'PPH 26', center_bold_2D75B5_white)
		worksheet.merge_range('AI4:AI5', 'PPH 4(2)', center_bold_2D75B5_white)
		worksheet.merge_range('AJ4:AJ5', 'KET', center_bold_5B9BD5_black)
		worksheet.merge_range('AK4:AK5', '', center_bold_5B9BD5_black)

		worksheet.merge_range('AL3:AQ3', 'PPH (DIPOTONG LAWAN TRANSAKSI) KREDIT PAJAK PT (UM PPH 23)', center_bold_yellow_black)
		worksheet.merge_range('AL4:AL5', 'DPP PPH 22/23', center_bold_yellow_black)
		worksheet.merge_range('AM4:AM5', 'PPh PASAL 22/23', center_bold_yellow_black)
		worksheet.merge_range('AN4:AN5', 'NOMOR BUKTI POTONG', center_bold_yellow_black)
		worksheet.merge_range('AO4:AO5', 'TANGGAL BUKTI POTONG', center_bold_yellow_black)
		worksheet.merge_range('AP4:AP5', 'MASA', center_bold_yellow_black)
		worksheet.merge_range('AQ4:AQ5', 'KET.', center_bold_yellow_black)

		worksheet.merge_range('AR3:AR5', 'KETERANGAN', center_bold_7F7F7F)

		worksheet.merge_range('AT3:AT5', 'KODE SUPPLIER', center_no_bold)
		worksheet.merge_range('AU3:AX3', 'JUMLAH', center_no_bold)
		worksheet.merge_range('AU4:AV4', 'PIUTANG', center_no_bold)
		worksheet.merge_range('AW4:AX4', 'HUTANG', center_no_bold)
		worksheet.write('AU5', 'SALDO AWAL', center_no_bold)
		worksheet.write('AV5', 'TOTAL PIUTANG', center_no_bold)
		worksheet.write('AW5', 'SALDO AWAL', center_no_bold)
		worksheet.write('AX5', 'TOTAL HUTANG', center_no_bold)
		worksheet.merge_range('AY3:AZ4', 'KAS/BANK', center_no_bold)
		worksheet.write('AY5', 'TANGGAL PEMBAYARAN', center_no_bold)
		worksheet.write('AZ5', 'JUMLAH PEMBAYARAN', center_no_bold)
		worksheet.merge_range('BA3:BB4', 'SISA OUTSTANDING', center_no_bold)
		worksheet.write('BA5', 'PIUTANG', center_no_bold)
		worksheet.write('BB5', 'HUTANG', center_no_bold)

		workbook.close()
		out = base64.b64encode(fp.getvalue())
		fp.close()
		filename = ('LIST_KODE_BARANG_BAHAN_BAKU.xlsx')
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