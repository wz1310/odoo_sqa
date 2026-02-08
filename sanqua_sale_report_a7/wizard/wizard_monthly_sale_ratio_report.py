# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

import base64
from datetime import datetime
from io import BytesIO

_logger = logging.getLogger(__name__)

class MonthlySaleRatioReportWizard(models.TransientModel):
    _name = 'monthly.sale.ratio.report.wizard'
    _description = 'Wizard Monthly Sale Ratio Report'
    YEARS = [(str(num), str(num)) for num in range(2020, (datetime.now().year)+1 )]

    year = fields.Selection(YEARS, string='Periode',required=True)
    free = fields.Selection([('actual','Actual (Exclude Free)'),('free','Free Product')], string='Product',required=True)
    name = fields.Char(string="Filename", readonly=True)
    data_file = fields.Binary(string="File", readonly=True)
    month_1 = fields.Selection([('1', 'JANUARI'), ('2', 'FEBRUARI'), ('3', 'MARET'), ('4', 'APRIL'),
                          ('5', 'MEI'), ('6', 'JUNI'), ('7', 'JULI'), ('8', 'AGUSTUS'), 
                          ('9', 'SEPTEMBER'), ('10', 'OKTOBER'), ('11', 'NOVEMBER'), ('12', 'DESEMBER'),], 
                          string='Month 1')
    month_2 = fields.Selection([('1', 'JANUARI'), ('2', 'FEBRUARI'), ('3', 'MARET'), ('4', 'APRIL'),
                          ('5', 'MEI'), ('6', 'JUNI'), ('7', 'JULI'), ('8', 'AGUSTUS'), 
                          ('9', 'SEPTEMBER'), ('10', 'OKTOBER'), ('11', 'NOVEMBER'), ('12', 'DESEMBER'),], 
                          string='Month 2')

    def btn_confirm(self):
        free = 'AND so_line.price_unit = 0'
        if self.free == 'actual':
            free = 'AND so_line.price_unit > 0'
        query = """
            SELECT rp.code, rp.name as partner,rm.name as region ,cg.name as group_customer, pp.default_code, pt.name as product,
                    sum(sr.qty_invoiced) FILTER (WHERE to_char(sr.date,'YYYY') = %s AND to_char(sr.date,'MM') = '01') AS januari,
                    sum(sr.qty_invoiced) FILTER (WHERE to_char(sr.date,'YYYY') = %s AND to_char(sr.date,'MM') = '02')AS februari,
                    sum(sr.qty_invoiced) FILTER (WHERE to_char(sr.date,'YYYY') = %s AND to_char(sr.date,'MM') = '03')AS maret,
                    sum(sr.qty_invoiced) FILTER (WHERE to_char(sr.date,'YYYY') = %s AND to_char(sr.date,'MM') = '04')AS april,
                    sum(sr.qty_invoiced) FILTER (WHERE to_char(sr.date,'YYYY') = %s AND to_char(sr.date,'MM') = '05')AS mei,
                    sum(sr.qty_invoiced) FILTER (WHERE to_char(sr.date,'YYYY') = %s AND to_char(sr.date,'MM') = '06')AS juni,
                    sum(sr.qty_invoiced) FILTER (WHERE to_char(sr.date,'YYYY') = %s AND to_char(sr.date,'MM') = '07')AS juli,
                    sum(sr.qty_invoiced) FILTER (WHERE to_char(sr.date,'YYYY') = %s AND to_char(sr.date,'MM') = '08')AS agustus,
                    sum(sr.qty_invoiced) FILTER (WHERE to_char(sr.date,'YYYY') = %s AND to_char(sr.date,'MM') = '09')AS september,
                    sum(sr.qty_invoiced) FILTER (WHERE to_char(sr.date,'YYYY') = %s AND to_char(sr.date,'MM') = '10')AS oktober,
                    sum(sr.qty_invoiced) FILTER (WHERE to_char(sr.date,'YYYY') = %s AND to_char(sr.date,'MM') = '11')AS november,
                    sum(sr.qty_invoiced) FILTER (WHERE to_char(sr.date,'YYYY') = %s AND to_char(sr.date,'MM') = '12')AS desember
            FROM sale_report sr
            JOIN res_partner rp ON rp.id = sr.partner_id
            LEFT JOIN sale_order so ON so.id = sr.order_id
            LEFT JOIN sale_order_line so_line ON so_line.order_id = so.id
            JOIN region_master rm ON rm.id = rp.region_master_id
            LEFT JOIN partner_pricelist pprice ON pprice.partner_id = rp.id and so.team_id = pprice.team_id
            LEFT JOIN customer_group cg ON pprice.customer_group = cg.id
            LEFT JOIN product_product pp ON pp.id = sr.product_id
            LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
            JOIN product_category pc ON pc.id = pt.categ_id
            WHERE pc.carton = FALSE 
            GROUP BY rp.code, rp.name,rm.name,cg.name,pt.name,pp.default_code;
        """
        
        new_query = """
            SELECT rp.code, rp.name as partner,rm.name as region ,cg.name as group_customer, pp.default_code, pt.name as product,
                    sum(so_line.qty_invoiced) FILTER (WHERE to_char(so.effective_date,'YYYY') = %s AND to_char(so.effective_date,'MM') = '01') AS januari,
                    sum(so_line.qty_invoiced) FILTER (WHERE to_char(so.effective_date,'YYYY') = %s AND to_char(so.effective_date,'MM') = '02')AS februari,
                    sum(so_line.qty_invoiced) FILTER (WHERE to_char(so.effective_date,'YYYY') = %s AND to_char(so.effective_date,'MM') = '03')AS maret,
                    sum(so_line.qty_invoiced) FILTER (WHERE to_char(so.effective_date,'YYYY') = %s AND to_char(so.effective_date,'MM') = '04')AS april,
                    sum(so_line.qty_invoiced) FILTER (WHERE to_char(so.effective_date,'YYYY') = %s AND to_char(so.effective_date,'MM') = '05')AS mei,
                    sum(so_line.qty_invoiced) FILTER (WHERE to_char(so.effective_date,'YYYY') = %s AND to_char(so.effective_date,'MM') = '06')AS juni,
                    sum(so_line.qty_invoiced) FILTER (WHERE to_char(so.effective_date,'YYYY') = %s AND to_char(so.effective_date,'MM') = '07')AS juli,
                    sum(so_line.qty_invoiced) FILTER (WHERE to_char(so.effective_date,'YYYY') = %s AND to_char(so.effective_date,'MM') = '08')AS agustus,
                    sum(so_line.qty_invoiced) FILTER (WHERE to_char(so.effective_date,'YYYY') = %s AND to_char(so.effective_date,'MM') = '09')AS september,
                    sum(so_line.qty_invoiced) FILTER (WHERE to_char(so.effective_date,'YYYY') = %s AND to_char(so.effective_date,'MM') = '10')AS oktober,
                    sum(so_line.qty_invoiced) FILTER (WHERE to_char(so.effective_date,'YYYY') = %s AND to_char(so.effective_date,'MM') = '11')AS november,
                    sum(so_line.qty_invoiced) FILTER (WHERE to_char(so.effective_date,'YYYY') = %s AND to_char(so.effective_date,'MM') = '12')AS desember
            FROM sale_order_line so_line
            LEFT JOIN sale_order so ON so.id = so_line.order_id
            LEFT JOIN res_partner rp ON rp.id = so.partner_id
            LEFT JOIN region_master rm ON rm.id = rp.region_master_id
            LEFT JOIN partner_pricelist pprice ON pprice.partner_id = rp.id and so.team_id = pprice.team_id
            LEFT JOIN customer_group cg ON pprice.customer_group = cg.id
            LEFT JOIN product_product pp ON pp.id = so_line.product_id
            LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
            JOIN product_category pc ON pc.id = pt.categ_id
            WHERE pc.carton = FALSE """+free+"""
            GROUP BY rp.code, rp.name,rm.name,cg.name,pt.name,pp.default_code;
        """
        
        param = []
        for rec in range(0,12):
            param.append(self.year)
        self.env.cr.execute(new_query, param)
        query_res = self.env.cr.fetchall()
        return self.generate_excel(query_res)

    
    def generate_excel(self, data):
        """ Generate excel based from label.print record. """
        MONTH = ['JANUARI','FEBRUARI','MARET','APRIL','MEI','JUNI','JULI',
            'AGUSTUS','SEPTEMBER','OKTOBER','NOVEMBER','DESEMBER']
        
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        worksheet = workbook.add_worksheet()
        str_month_1 = dict(self._fields['month_1'].selection).get(self.month_1)
        str_month_2 = dict(self._fields['month_2'].selection).get(self.month_2)
        # =============== HEADER ===============
        header_format = workbook.add_format({'bold': True,'align':'center'})
        center_format = workbook.add_format({'align':'center'})
        worksheet.set_column('A4:A4', 15)
        worksheet.set_column('B4:B4', 30)
        worksheet.set_column('C4:C4', 10)
        worksheet.set_column('D4:E4', 15)
        worksheet.set_column('F4:F4', 30)
        worksheet.set_column('G4:R4', 10)
        worksheet.set_column('U:U', 30)
        worksheet.merge_range('A1:R2','LAPORAN PERBANDINGAN PENJUALAN PERBULAN '+self.free+'\n'+self.year,header_format)
        worksheet.write(3, 0, "Kode Pelanggan",center_format)
        worksheet.write(3, 1, "Nama Pelanggan",center_format)
        worksheet.write(3, 2, "Area",center_format)
        worksheet.write(3, 3, "Class Outlet",center_format)
        worksheet.write(3, 4, "Kode Barang",center_format)
        worksheet.write(3, 5, "Nama Barang",center_format)
        worksheet.write(3, 6, "JANUARI",center_format)
        worksheet.write(3, 7, "FEBRUARI",center_format)
        worksheet.write(3, 8, "MARET",center_format)
        worksheet.write(3, 9, "APRIL",center_format)
        worksheet.write(3, 10, "MEI",center_format)
        worksheet.write(3, 11, "JUNI",center_format)
        worksheet.write(3, 12, "JULI",center_format)
        worksheet.write(3, 13, "AGUSTUS",center_format)
        worksheet.write(3, 14, "SEPTEMBER",center_format)
        worksheet.write(3, 15, "OKTOBER",center_format)
        worksheet.write(3, 16, "NOVEMBER",center_format)
        worksheet.write(3, 17, "DESEMBER",center_format)
        worksheet.write(3, 18, "MAX QTY",center_format)
        worksheet.write(3, 19, "MAX MONTH",center_format)
        worksheet.write(3, 20, "PERBANDINGAN " + str_month_1 + ' / ' + str_month_2,center_format)
        # =============== HEADER ===============

        # =============== BODY ===============
        format_right = workbook.add_format({'align': 'right'})
        bulan_1 = int(self.month_1) + 5
        bulan_2 = int(self.month_2) + 5
        row_idx = 4
        
        for line in data:
            hasil_perbandingan = 0.0
            max_qty = []
            if line[bulan_1] and line[bulan_1] > 0.0 and line[bulan_2] and line[bulan_2] > 0.0:
                hasil_perbandingan = round(line[bulan_1] / line[bulan_2], 2)
            
            worksheet.write(row_idx, 0, line[0])
            worksheet.write(row_idx, 1, line[1])
            worksheet.write(row_idx, 2, line[2],center_format)
            worksheet.write(row_idx, 3, line[3])
            worksheet.write(row_idx, 4, line[4],center_format)
            worksheet.write(row_idx, 5, line[5])
            worksheet.write(row_idx, 6, line[6],center_format) #Januari
            worksheet.write(row_idx, 7, line[7],center_format) #Februari
            worksheet.write(row_idx, 8, line[8],center_format) 
            worksheet.write(row_idx, 9, line[9],center_format)
            worksheet.write(row_idx, 10, line[10],center_format)
            worksheet.write(row_idx, 11, line[11],center_format)
            worksheet.write(row_idx, 12, line[12],center_format)
            worksheet.write(row_idx, 13, line[13],center_format)
            worksheet.write(row_idx, 14, line[14],center_format)
            worksheet.write(row_idx, 15, line[15],center_format)
            worksheet.write(row_idx, 16, line[16],center_format)
            worksheet.write(row_idx, 17, line[17],center_format)
            for x in range(6,18):
                max_qty.append(line[x] or 0.0)
            idx_month = max_qty.index(max(max_qty))
            worksheet.write(row_idx, 18, max(max_qty),center_format)
            worksheet.write(row_idx, 19, MONTH[idx_month],center_format)
            worksheet.write(row_idx, 20, hasil_perbandingan,center_format)
            row_idx += 1
        # =============== BODY ===============

        workbook.close()
        out = base64.b64encode(fp.getvalue())
        fp.close()
        filename = ('monthly_sale_ratio_%s.xlsx')%(self.year)
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

    