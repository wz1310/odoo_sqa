# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
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


class WizardDailyOrderA17Report(models.TransientModel):
	_name = 'wizard.daily.order.a17.report'
	_description = 'Wizard Daily Order A17 Report'

	date_start = fields.Date('Start Date', required=True)
	date_end = fields.Date('End Date', required=True)
	company_id = fields.Many2one('res.company',
								 string='Company',
								 required=True)
	name = fields.Char(string="Filename", readonly=True)
	data_file = fields.Binary(string="File", readonly=True)

	def button_print(self):
		data = self._get_data_product()
		return self.generate_excel(data)

	def btn_confirm(self):
		# At: 17/01/2023
		# Description: Old version from PCI
		# query = """
		# 	SELECT so.name, so.commitment_date_mask, comp.name as plant, partner.code as kode_divisi, partner.name as customer, 
		# 		sales.name as salesperson, team.name as divisi, prod_tmpl.name as product, sm.product_uom_qty as qty, fleet.name as mobil, 
    	# 		delivery_address.city as tujuan, so.internal_sale_notes as keterangan
		# 	FROM stock_move sm
		# 	JOIN stock_picking sp on sm.picking_id = sp.id
		# 	JOIN sale_order_line so_line on so_line.id = sm.sale_line_id
		# 	JOIN sale_order so on so.id = so_line.order_id
		# 	JOIN product_product product on product.id = sm.product_id
		# 	JOIN product_template prod_tmpl on prod_tmpl.id = product.product_tmpl_id
		# 	JOIN res_company comp on comp.id = so.company_id
		# 	JOIN res_partner partner on so.partner_id = partner.id
		# 	JOIN crm_team team on team.id = so.team_id
		# 	JOIN res_users user_odoo on user_odoo.id = so.user_id
		# 	JOIN res_partner sales on sales.id = user_odoo.partner_id
		# 	JOIN fleet_vehicle_model fleet on fleet.id = so.vehicle_model_id
		# 	JOIN res_partner delivery_address on delivery_address.id = so.partner_shipping_id
		# 	where sp.doc_name = 'New' and so.commitment_date_mask >= %s and so.commitment_date_mask <= %s and so.company_id = %s
		# """

		# At: 17/01/2023
		# Description: New Version from MIS
		query = """
			SELECT
				so.NAME,
				sale_order_mix.name AS "so_sale_order_mix",
				(so.create_date + INTERVAL '7 hours') AS create_date,
				so.commitment_date_mask,	
				
			-- 	comp.NAME AS plant,
				partner.code AS kode_divisi,
				partner.NAME AS customer,
				sales.NAME AS salesperson,
				team.NAME AS divisi,
				-- prod_tmpl.NAME AS product,
				so_line.name AS "product",
				so_line.product_uom_qty AS qty,
				fleet.NAME AS mobil,
				CONCAT('(',delivery_address.name,')', delivery_address.street) AS tujuan,
				so.internal_sale_notes AS keterangan,
				
				-- 	Additional Column
				CASE WHEN CURRENT_DATE > commitment_date_mask THEN 'Pending' ELSE 'Normal' END AS "priority",
				rc.id AS "plant_id",
				rc.name AS "plant_name"				

			FROM
				sale_order so LEFT JOIN sale_order_line so_line ON so.id = so_line.order_id
				LEFT JOIN product_product product ON product.ID = so_line.product_id
				LEFT JOIN product_template prod_tmpl ON prod_tmpl.ID = product.product_tmpl_id
				LEFT JOIN res_company comp ON comp.id = so.company_id
				LEFT JOIN res_partner partner ON so.partner_id = partner.id JOIN crm_team team ON team.id = so.team_id
				LEFT JOIN res_users user_odoo ON user_odoo.id = so.user_id
				LEFT JOIN res_partner sales ON sales.id = user_odoo.partner_id
				LEFT JOIN fleet_vehicle_model fleet ON fleet.id = so.vehicle_model_id
				LEFT JOIN res_partner delivery_address ON delivery_address.id = so.partner_shipping_id 
				-- Additional column purpose
				LEFT JOIN (
					SELECT so.id, so.name, somr.sale_order_id
					FROM sale_order so LEFT JOIN sale_order_mix_rel somr ON so.id = somr.mix_id
				) sale_order_mix ON so.id = sale_order_mix.sale_order_id
				LEFT JOIN res_company rc ON rc.id = so.plant_id
			WHERE
			-- Old version
			-- 	sp.doc_name = 'New' 
			
				so.commitment_date_mask >= %s
				AND so.commitment_date_mask <= %s
				AND so.validity_date >= CURRENT_DATE
				AND so.state = 'sale'
				AND so.company_id = 2
				AND so.plant_id = %s
		"""

		param = (self.date_start, self.date_end, self.company_id.id)
		
		query_delivery = query + """ AND so.order_pickup_method_id = 1 AND so_line.qty_delivered = 0 ORDER BY create_date""" 

		#Request by Mas Adi at 19/01/2023: Only take in plant that still showing until it expire
		query_take_in_plant = query + """ AND so.order_pickup_method_id = 2 """
		self.env.cr.execute(query_delivery, param)
		query_res = self.env.cr.fetchall()

		self.env.cr.execute(query_take_in_plant, param)
		query_res_take_in_plant = self.env.cr.fetchall()
		return self.generate_excel(query_res, query_res_take_in_plant)

	def generate_excel(self, data, data_take_in_plant):
		""" Generate excel based from label.print record. """
		fp = BytesIO()
		xCurrentColor = '#D7DADB'
		xCurrentSONo = ''

		workbook = xlsxwriter.Workbook(fp)
		workbook.formats[0].set_font_name('Arial')
		##################################################################
		normal_style = workbook.add_format({'valign':'vcenter', 'border':1,
			'font_name':'Arial', 'font_size':10})
		normal_style.set_text_wrap()
		#################################################################################
		bold_style = workbook.add_format({'bold': 1, 'valign':'vcenter', 'border':1,
			'font_name':'Arial', 'font_size':10})
		bold_style.set_text_wrap()
		#################################################################################
		bolder_style = workbook.add_format({'bold': 1, 'valign':'vcenter', 'border':1,
			'font_name':'Arial', 'font_size':11})
		bolder_style.set_text_wrap()
		#################################################################################
		center_style = workbook.add_format({'valign':'vcenter', 'align':'center', 'border':1,
			'font_name':'Arial', 'font_size':10})
		center_style.set_text_wrap()
		#################################################################################
		b_center_style = workbook.add_format({'bold': 1, 'valign':'vcenter', 'align':'center',
			'border':1, 'font_name':'Arial', 'font_size':10})
		b_center_style.set_text_wrap()
		#################################################################################
		right_style = workbook.add_format({'valign':'vcenter', 'align':'right', 'border':1,
			'num_format': '#,##0', 'font_name':'Arial', 'font_size':10})
		right_style.set_text_wrap()
		#################################################################################
		normal_style_date = workbook.add_format({'valign':'vcenter', 'border':1, 'text_wrap':True,
			'font_size':11, 'font_name': 'Arial', 'num_format': 'dd/mm/yyyy'})

		normal_style_datetime = workbook.add_format({'valign':'vcenter', 'border':1, 'text_wrap':True,
			'font_size':11, 'font_name': 'Arial', 'num_format': 'dd/mm/yyyy hh:mm'})
  
		worksheet = workbook.add_worksheet('Delivery')
		worksheet_2 = workbook.add_worksheet('Take In Plant')
		worksheet_3 = workbook.add_worksheet('Summary SO Delivery')

		# =============== HEADER ===============
		header_format = workbook.add_format({'bold': True,'align':'center'})
		center_format = workbook.add_format({'align':'center'})
		worksheet.set_column('A:Z', 20)
		worksheet.merge_range('A1:R2','Report SO')
		worksheet.write(3, 0, "No SO",bolder_style)
		worksheet.write(3, 1, "SO Mix",bolder_style)
		worksheet.write(3, 2, "Tgl Order",bolder_style)
		worksheet.write(3, 3, "Tanggal Kirim",bolder_style)
		worksheet.write(3, 4, "Prioritas Kirim",bolder_style)
		worksheet.write(3, 5, "Plant",bolder_style)
		worksheet.write(3, 6, "Kode Customer",bolder_style)
		worksheet.write(3, 7, "Nama Customer",bolder_style)
		worksheet.write(3, 8, "Sales",bolder_style)
		worksheet.write(3, 9, "Divisi",bolder_style)
		worksheet.write(3, 10, "Size",bolder_style)
		worksheet.write(3, 11, "Qty",bolder_style)
		worksheet.write(3, 12, "Jenis Mobil",bolder_style)
		worksheet.write(3, 13, "Tujuan Kirim",bolder_style)
		worksheet.write(3, 14, "Keterangan",bolder_style)
		worksheet.write(3, 15, "No. Pol",bolder_style)
		worksheet.write(3, 16, "Supir",bolder_style)

		worksheet_2.set_column('A:Z', 20)
		worksheet_2.merge_range('A1:R2','Report SO')
		worksheet_2.write(3, 0, "No SO",bolder_style)
		worksheet_2.write(3, 1, "SO Mix",bolder_style)
		worksheet_2.write(3, 2, "Tgl Order",bolder_style)
		worksheet_2.write(3, 3, "Tanggal Kirim",bolder_style)
		worksheet_2.write(3, 4, "Prioritas Kirim",bolder_style)
		worksheet_2.write(3, 5, "Plant",bolder_style)
		worksheet_2.write(3, 6, "Kode Customer",bolder_style)
		worksheet_2.write(3, 7, "Nama Customer",bolder_style)
		worksheet_2.write(3, 8, "Sales",bolder_style)
		worksheet_2.write(3, 9, "Divisi",bolder_style)
		worksheet_2.write(3, 10, "Size",bolder_style)
		worksheet_2.write(3, 11, "Qty",bolder_style)
		worksheet_2.write(3, 12, "Jenis Mobil",bolder_style)
		worksheet_2.write(3, 13, "Tujuan Kirim",bolder_style)
		worksheet_2.write(3, 14, "Keterangan",bolder_style)
		worksheet.write(3, 15, "No. Pol",bolder_style)
		worksheet.write(3, 16, "Supir",bolder_style)

		worksheet_3.set_column('A:Z', 20)
		worksheet_3.merge_range('A1:R2','Report Summary SO Delivery')
		worksheet_3.write(3, 0, "No SO",bolder_style)
		worksheet_3.write(3, 1, "Tgl Order",bolder_style)
		worksheet_3.write(3, 2, "Tgl Kirim",bolder_style)
		worksheet_3.write(3, 3, "Customer",bolder_style)
		worksheet_3.write(3, 4, "Tujuan kirim",bolder_style)
		worksheet_3.write(3, 5, "Mobil",bolder_style)
		# =============== HEADER ===============

		# =============== BODY ===============
		format_right = workbook.add_format({'align': 'right'})

		# Delivery Section
		row_idx = 4
		for line in data:
			normal_style.set_pattern(1)
			if xCurrentSONo == '':				
				xCurrentSONo = '#D7DADB'
			else:
				if line[0] != xCurrentSONo:
					if xCurrentColor == '#D7DADB':
						xCurrentColor = '#FFFFFF'
						# normal_style.set_bg_color(xCurrentColor)
											
					else:
						xCurrentColor = '#D7DADB'
						# normal_style.set_bg_color(xCurrentColor)
						
			normal_style = workbook.add_format({'bg_color':xCurrentColor,'valign':'vcenter', 'border':1,'font_name':'Arial', 'font_size':10})
			normal_style_date = workbook.add_format({'bg_color':xCurrentColor,'valign':'vcenter', 'border':1, 'text_wrap':True,'font_size':11, 'font_name': 'Arial', 'num_format': 'dd/mm/yyyy'})
			normal_style_datetime = workbook.add_format({'bg_color':xCurrentColor,'valign':'vcenter', 'border':1, 'text_wrap':True,'font_size':11, 'font_name': 'Arial', 'num_format': 'dd/mm/yyyy hh:mm'})
			normal_style.set_text_wrap()	

			# print('>>> xCurrentSoNo : ' + str(xCurrentSONo))
			# print('>>> line[0] : ' + str(line[0]))
			# print('>>> xCurrentColor : ' + str(xCurrentColor))
			# print('>>> -------------------------------------')

			worksheet.write(row_idx, 0, line[0], normal_style)
			worksheet.write(row_idx, 1, line[1], normal_style)
			worksheet.write(row_idx, 2, line[2], normal_style_datetime)
			worksheet.write(row_idx, 3, line[3], normal_style_date)
			worksheet.write(row_idx, 4, line[13], normal_style)
			worksheet.write(row_idx, 5, line[15], normal_style)
			worksheet.write(row_idx, 6, line[4], normal_style)
			worksheet.write(row_idx, 7, line[5], normal_style)
			worksheet.write(row_idx, 8, line[6], normal_style)
			worksheet.write(row_idx, 9, line[7], normal_style)
			worksheet.write(row_idx, 10, line[8], normal_style)
			worksheet.write(row_idx, 11, line[9], normal_style)
			worksheet.write(row_idx, 12, line[10], normal_style)
			worksheet.write(row_idx, 13, line[11], normal_style)
			worksheet.write(row_idx, 14, line[12], normal_style)	
			row_idx += 1

			xCurrentSONo = line[0]
		# =============== BODY ===============

		# Take in Plant Section
		row_idx = 4
		xCurrentSONo = ''
		xCurrentColor = '#D7DADB'
		for line in data_take_in_plant:
			normal_style.set_pattern(1)
			if xCurrentSONo == '':				
				xCurrentSONo = '#D7DADB'
			else:
				if line[0] != xCurrentSONo:
					if xCurrentColor == '#D7DADB':
						xCurrentColor = '#FFFFFF'
						# normal_style.set_bg_color(xCurrentColor)
											
					else:
						xCurrentColor = '#D7DADB'
						# normal_style.set_bg_color(xCurrentColor)
						
			normal_style = workbook.add_format({'bg_color':xCurrentColor,'valign':'vcenter', 'border':1,'font_name':'Arial', 'font_size':10})
			normal_style_date = workbook.add_format({'bg_color':xCurrentColor,'valign':'vcenter', 'border':1, 'text_wrap':True,'font_size':11, 'font_name': 'Arial', 'num_format': 'dd/mm/yyyy'})
			normal_style_datetime = workbook.add_format({'bg_color':xCurrentColor,'valign':'vcenter', 'border':1, 'text_wrap':True,'font_size':11, 'font_name': 'Arial', 'num_format': 'dd/mm/yyyy hh:mm'})
			normal_style.set_text_wrap()	

			# print('>>> xCurrentSoNo : ' + str(xCurrentSONo))
			# print('>>> line[0] : ' + str(line[0]))
			# print('>>> xCurrentColor : ' + str(xCurrentColor))
			# print('>>> -------------------------------------')

			worksheet_2.write(row_idx, 0, line[0], normal_style)
			worksheet_2.write(row_idx, 1, line[1], normal_style)
			worksheet_2.write(row_idx, 2, line[2], normal_style_datetime)
			worksheet_2.write(row_idx, 3, line[3], normal_style_date)
			worksheet_2.write(row_idx, 4, line[13], normal_style)
			worksheet_2.write(row_idx, 5, line[15], normal_style)
			worksheet_2.write(row_idx, 6, line[4], normal_style)
			worksheet_2.write(row_idx, 7, line[5], normal_style)
			worksheet_2.write(row_idx, 8, line[6], normal_style)
			worksheet_2.write(row_idx, 9, line[7], normal_style)
			worksheet_2.write(row_idx, 10, line[8], normal_style)
			worksheet_2.write(row_idx, 11, line[9], normal_style)
			worksheet_2.write(row_idx, 12, line[10], normal_style)
			worksheet_2.write(row_idx, 13, line[11], normal_style)
			worksheet_2.write(row_idx, 14, line[12], normal_style)	
			row_idx += 1

			xCurrentSONo = line[0]

		# =============== Summary ===============
		row_idx = 4
		xCurrentSONo = ''
		xCurrentColor = '#D7DADB'
		# print("DATA", data)
		# K = [*set([x[0] for x in data])]
		n_data = [{'nm':x[0],'tgl':x[2],'tgl_krm': x[3],'cst': x[5],'tju': x[11],'mbl': x[10]} for x in data]
		res_list = []
		for i in range(len(n_data)):
			if n_data[i] not in n_data[i + 1:]:
				res_list.append(n_data[i])
		# print(res_list)
		for x in res_list:
			worksheet_3.write(row_idx, 0, x['nm'], normal_style)	
			worksheet_3.write(row_idx, 1, x['tgl'], normal_style_datetime)
			worksheet_3.write(row_idx, 2, x['tgl_krm'], normal_style)
			worksheet_3.write(row_idx, 3, x['cst'], normal_style)
			worksheet_3.write(row_idx, 4, x['tju'], normal_style)
			worksheet_3.write(row_idx, 5, x['mbl'], normal_style)
			row_idx += 1
		# =============== BODY ===============

		workbook.close()
		out = base64.b64encode(fp.getvalue())
		fp.close()
		filename = 'report_so_a17.xlsx'
		return self.set_data_excel(out, filename)

	def set_data_excel(self, out, filename):
		""" Update data_file and name based from previous process output. And return action url for download excel. """
		self.write({
			'data_file': out,
			'name': filename
		})

		return {
			'type': 'ir.actions.act_url',
			'name': filename,
			'url': '/web/content/%s/%s/data_file/%s' % (self._name, self.id, filename,),
		}