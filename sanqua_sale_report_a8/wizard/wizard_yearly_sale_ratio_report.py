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

class YearlySaleRatioReportWizard(models.TransientModel):
    _name = 'yearly.sale.ratio.report.wizard'
    _description = 'Wizard Yearly Sale Ratio Report'
    YEARS = [(str(num), str(num)) for num in range(2020, (datetime.now().year)+1 )]

    start_year = fields.Selection(YEARS, string='Periode',required=True)
    end_year = fields.Selection(YEARS, string='Periode',required=True)
    name = fields.Char(string="Filename", readonly=True)
    data_file = fields.Binary(string="File", readonly=True)

    def _select_year(self):
        str_year = ''
        for rec in range(int(self.start_year),int(self.end_year)+1):
            str_year += (""",sum(qty_invoiced) FILTER (WHERE to_char(sr.date,'YYYY') = '%s') AS tahun_%s""") %(str(rec),str(rec),)
        return str_year

    def btn_confirm(self):
        query = """
            SELECT rp.code, rp.name as partner,rm.name as region ,cg.name as group_customer, pp.default_code, pt.name as product """ + self._select_year() +"""
            FROM sale_report sr
            JOIN res_partner rp ON rp.id = sr.partner_id
            LEFT JOIN sale_order so ON so.id = sr.order_id
            JOIN region_master rm ON rm.id = rp.region_master_id
            LEFT JOIN partner_pricelist pprice ON pprice.partner_id = rp.id and so.team_id = pprice.team_id
            LEFT JOIN customer_group cg ON pprice.customer_group = cg.id
            LEFT JOIN product_product pp ON pp.id = sr.product_id
            LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
            JOIN product_category pc ON pc.id = pt.categ_id
            WHERE pc.carton = FALSE
            GROUP BY rp.code, rp.name,rm.name,cg.name,pt.name,pp.default_code;
        """
        self.env.cr.execute(query)
        query_res = self.env.cr.fetchall()
        return self.generate_excel(query_res)

    
    def generate_excel(self, data):
        """ Generate excel based from label.print record. """
        MONTH = ['JANUARI','FEBRUARI','MARET','APRIL','MEI','JUNI','JULI',
            'AGUSTUS','SEPTEMBER','OKTOBER','NOVEMBER','DESEMBER']
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        worksheet = workbook.add_worksheet()

        # =============== HEADER ===============
        header_format = workbook.add_format({'bold': True,'align':'center'})
        center_format = workbook.add_format({'align':'center'})
        right_num_format = workbook.add_format({'align':'right'})
        right_num_format.set_num_format('#,##0.00')
        worksheet.set_column('A4:A4', 15)
        worksheet.set_column('B4:B4', 30)
        worksheet.set_column('C4:C4', 10)
        worksheet.set_column('D4:E4', 15)
        worksheet.set_column('F4:F4', 30)
        worksheet.set_column('G4:R4', 10)
        worksheet.write(3, 0, "Kode Pelanggan",center_format)
        worksheet.write(3, 1, "Nama Pelanggan",center_format)
        worksheet.write(3, 2, "Area",center_format)
        worksheet.write(3, 3, "Class Outlet",center_format)
        worksheet.write(3, 4, "Kode Barang",center_format)
        worksheet.write(3, 5, "Nama Barang",center_format)
        count_year = 6
        for rec in range(int(self.start_year),int(self.end_year)+1):
            worksheet.write(3, count_year, rec,center_format)
            count_year += 1
        count_perbandingan = count_year
        last_year = ''
        for rec in range(int(self.start_year),int(self.end_year)+1):
            if rec > int(self.start_year):
                worksheet.write(3, count_perbandingan, ("TH %s/TH %s")%(last_year,str(rec)),center_format)
                count_perbandingan += 1
            last_year = str(rec)
        # =============== HEADER ===============

        # =============== BODY ===============
        format_right = workbook.add_format({'align': 'right'})

        row_idx = 4
        for line in data:
            max_qty = []
            worksheet.write(row_idx, 0, line[0])
            worksheet.write(row_idx, 1, line[1])
            worksheet.write(row_idx, 2, line[2],center_format)
            worksheet.write(row_idx, 3, line[3])
            worksheet.write(row_idx, 4, line[4],center_format)
            worksheet.write(row_idx, 5, line[5])
            col_year = 6
            for rec in range(int(self.start_year),int(self.end_year)+1):
                val = 0
                if line[col_year]:
                    val = line[col_year]
                worksheet.write(row_idx, col_year, val,right_num_format)
                col_year += 1
            col_year_perbandingan = 6
            col_perbandingan = col_year
            val_last_year = 0
            for rec in range(int(self.start_year),int(self.end_year)+1):
                if rec > int(self.start_year):
                    val = 0
                    if line[col_year_perbandingan] and val_last_year > 0:
                        val = (line[col_year_perbandingan] - val_last_year) / val_last_year * 100
                    worksheet.write(row_idx, col_perbandingan, val, right_num_format)
                    col_perbandingan += 1
                if line[col_year_perbandingan]:
                    val_last_year = line[col_year_perbandingan]
                col_year_perbandingan += 1
            row_idx += 1
        # =============== BODY ===============

        worksheet.merge_range(0,0,1,count_perbandingan-1,'LAPORAN PERBANDINGAN PENJUALAN Tahunan \n'+self.start_year +' - '+self.end_year,header_format)

        workbook.close()
        out = base64.b64encode(fp.getvalue())
        fp.close()
        filename = ('yearly_sale_ratio_%s_to_%s.xlsx')%(self.start_year,self.end_year)
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

    