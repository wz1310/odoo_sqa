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


class WizardDailyOrderA18Report(models.TransientModel):
    _name = 'wizard.daily.order.a18.report'
    _description = 'Wizard Daily Order a18 Report'

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
        query = """
            SELECT so.name, so.commitment_date_mask, comp.name as plant, partner.code as kode_divisi, partner.name as customer, 
                sales.name as salesperson, team.name as divisi, prod_tmpl.name as product, sm.product_uom_qty as qty, fleet.name as mobil, 
                delivery_address.city as tujuan, plat.license_plate as plat, sm.id as stock_move, sp.note
            FROM stock_move sm
			JOIN stock_picking sp on sm.picking_id = sp.id
			JOIN sale_order_line so_line on so_line.id = sm.sale_line_id
			JOIN sale_order so on so.id = so_line.order_id
			JOIN product_product product on product.id = sm.product_id
			JOIN product_template prod_tmpl on prod_tmpl.id = product.product_tmpl_id
			JOIN res_company comp on comp.id = so.company_id
			JOIN res_partner partner on so.partner_id = partner.id
			JOIN crm_team team on team.id = so.team_id
			JOIN res_users user_odoo on user_odoo.id = so.user_id
			JOIN res_partner sales on sales.id = user_odoo.partner_id
			JOIN fleet_vehicle_model fleet on fleet.id = so.vehicle_model_id
            JOIN fleet_vehicle plat on plat.id = sp.fleet_vehicle_id
			JOIN res_partner delivery_address on delivery_address.id = so.partner_shipping_id
            WHERE sp.doc_name != 'New' and so.commitment_date_mask >= %s and so.commitment_date_mask <= %s and so.company_id = %s
        """
        param = (self.date_start, self.date_end, self.company_id.id)
        self.env.cr.execute(query, param)
        query_res = self.env.cr.fetchall()
        return self.generate_excel(query_res)

    def generate_excel(self, data):
        """ Generate excel based from label.print record. """
        fp = BytesIO()
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
        worksheet = workbook.add_worksheet()

        # =============== HEADER ===============
        header_format = workbook.add_format({'bold': True,'align':'center'})
        center_format = workbook.add_format({'align':'center'})
        worksheet.set_column('A:Z', 20)
        worksheet.merge_range('A1:R2','Report OC')
        worksheet.write(3, 0, "No SO",bolder_style)
        worksheet.write(3, 1, "Tanggal Kirim",bolder_style)
        worksheet.write(3, 2, "Plant",bolder_style)
        worksheet.write(3, 3, "Kode Customer",bolder_style)
        worksheet.write(3, 4, "Nama Customer",bolder_style)
        worksheet.write(3, 5, "Sales",bolder_style)
        worksheet.write(3, 6, "Divisi",bolder_style)
        worksheet.write(3, 7, "Size",bolder_style)
        worksheet.write(3, 8, "Qty",bolder_style)
        worksheet.write(3, 9, "Jenis Mobil",bolder_style)
        worksheet.write(3, 10, "Tujuan Kirim",bolder_style)
        worksheet.write(3, 11, "No Mobil",bolder_style)
        worksheet.write(3, 12, "Retur",bolder_style)
        worksheet.write(3, 13, "Pengiriman Bersih",bolder_style)
        worksheet.write(3, 14, "Kendala Pengiriman",bolder_style)
        # =============== HEADER ===============

        # =============== BODY ===============
        format_right = workbook.add_format({'align': 'right'})

        row_idx = 4
        for line in data:
            return_qty = 0.0
            move_id = self.env['stock.move'].browse(line[12])
            if move_id and move_id.returned_move_ids:
                return_qty = sum(move_id.returned_move_ids.filtered(lambda self: self.state == 'done').mapped('quantity_done')) - sum(move_id.returned_move_ids.filtered(lambda self: self.state == 'done').mapped('return_qty'))
            worksheet.write(row_idx, 0, line[0], normal_style)
            worksheet.write(row_idx, 1, line[1], normal_style_date)
            worksheet.write(row_idx, 2, line[2], normal_style)
            worksheet.write(row_idx, 3, line[3], normal_style)
            worksheet.write(row_idx, 4, line[4], normal_style)
            worksheet.write(row_idx, 5, line[5], normal_style)
            worksheet.write(row_idx, 6, line[6], normal_style)
            worksheet.write(row_idx, 7, line[7], normal_style)
            worksheet.write(row_idx, 8, line[8], normal_style)
            worksheet.write(row_idx, 9, line[9], normal_style)
            worksheet.write(row_idx, 10, line[10], normal_style)
            worksheet.write(row_idx, 11, line[11], normal_style)
            worksheet.write(row_idx, 12, return_qty, normal_style)
            worksheet.write(row_idx, 13, line[8] - return_qty, normal_style)
            worksheet.write(row_idx, 14, line[13], normal_style)
            row_idx += 1
        # =============== BODY ===============

        workbook.close()
        out = base64.b64encode(fp.getvalue())
        fp.close()
        filename = 'report_oc_a18.xlsx'
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
