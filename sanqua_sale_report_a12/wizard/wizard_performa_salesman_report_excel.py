# -*- coding: utf-8 -*-
import base64
import datetime
import logging

from datetime import date
from io import BytesIO
from calendar import monthrange
from odoo import _, api, fields, models

try:
    from odoo.tools.misc import xlsxwriter
    from xlsxwriter.utility import xl_range
    from xlsxwriter.utility import xl_rowcol_to_cell
except ImportError:
    import xlsxwriter
    from xlsxwriter.utility import xl_range
    from xlsxwriter.utility import xl_rowcol_to_cell

class PerformaSalesmanReportWizard(models.TransientModel):
    _name = 'performa.salesman.report.excel.wizard'
    _description = 'Wizard Performa Salesman Excel Report'

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    tahun = fields.Integer(string='Tahun')
    bulan = fields.Integer(string='Bulan (1-12)')
    name = fields.Char(string="Filename", readonly=True)
    data_file = fields.Binary(string="File", readonly=True)

    @api.onchange('start_date','end_date')
    def _onchange_date(self):
        if self.start_date:
            self.start_date = datetime.date(self.start_date.year, self.start_date.month,1)
        if self.end_date:
            self.end_date =  datetime.date(self.end_date.year, self.end_date.month,monthrange(self.end_date.year, self.end_date.month)[1])

    def query_target_realisasi(self, new_params):
        query = """
            select
                tl.product_id,
                tl.user_id,
                sum(tl.qty) as qty_target,
                (SELECT sum(sr.qty_delivered) FROM sale_report sr 
                    WHERE sr.user_id = tl.user_id AND
                            EXTRACT(MONTH from sr.date) = %s AND EXTRACT(YEAR from sr.date) = %s
                            AND sr.product_id = tl.product_id) as qty_realisasi,
                (SELECT sum(sr.qty_delivered) FROM sale_report sr 
                    WHERE sr.user_id = tl.user_id AND
                            EXTRACT(MONTH from sr.date) = %s AND EXTRACT(YEAR from sr.date) = %s
                            AND sr.product_id = tl.product_id) / sum(tl.qty) * 100 as persentase,
                (SELECT ABS(sum(aml.balance)) from account_move_line aml 
                LEFT JOIN account_account aa ON aa.id = aml.account_id
                LEFT JOIN res_users users on users.id = tl.user_id
                LEFT JOIN res_partner partner on partner.id = users.partner_id
                WHERE aml.partner_id = partner.id AND aa.user_type_id = 15 AND
                    EXTRACT(MONTH from aml.date) = %s AND EXTRACT(YEAR from aml.date) = %s) as biaya
                FROM sales_user_target_line tl
                WHERE tl.month = '%s' AND tl.year = '%s' AND tl.user_id = %s AND tl.product_id = %s
                GROUP BY tl.user_id, tl.product_id, concat(tl.user_id, tl.product_id)
                ORDER BY tl.product_id, tl.user_id
        """
        params = (self.bulan, self.tahun, 
            self.bulan, self.tahun, 
            self.bulan, self.tahun, 
            self.bulan, self.tahun,
            )
        self._cr.execute(
            query,
            params + new_params,
        )
        target_result = self._cr.dictfetchall()
        return target_result

    def query_biaya(self, user_id):
        query = """
            select
                tl.product_id,
                tl.user_id,
                (SELECT ABS(sum(aml.balance)) from account_move_line aml 
                LEFT JOIN account_account aa ON aa.id = aml.account_id
                LEFT JOIN res_users users on users.id = tl.user_id
                LEFT JOIN res_partner partner on partner.id = users.partner_id
                WHERE aml.partner_id = partner.id AND aa.user_type_id = 15 AND
                    EXTRACT(MONTH from aml.date) = %s AND EXTRACT(YEAR from aml.date) = %s) as biaya
                FROM sales_user_target_line tl
                WHERE tl.month = '%s' AND tl.year = '%s' AND tl.user_id = %s
                GROUP BY tl.user_id, tl.product_id, concat(tl.user_id, tl.product_id)
                ORDER BY tl.product_id, tl.user_id
        """
        params = (self.bulan, self.tahun, 
                    self.bulan, self.tahun,
                )
        self._cr.execute(
            query,
            params + user_id,
        )
        target_result = self._cr.dictfetchall()
        if target_result:
            target_result = target_result[0]
        return target_result

    def query_limit(self, user_id):
        query = """
            select
                tl.user_id,
                (select ABS(sum(pp.credit_limit)) from partner_pricelist pp
                where pp.partner_id = tl.partner_id and pp.team_id = tl.team_id and pp.customer_group = tl.customer_group_id) as limit
                FROM sales_user_target_line tl
                WHERE tl.month = '%s' AND tl.year = '%s' AND tl.user_id = %s
                GROUP BY tl.user_id, tl.partner_id, tl.team_id, tl.customer_group_id
                Order by tl.user_id
        """
        params = (self.bulan, self.tahun,)
        self._cr.execute(
            query,
            params + user_id,
        )
        target_result = self._cr.dictfetchall()
        if target_result:
            target_result = target_result[0]
        return target_result
        
    def btn_confirm(self):
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        worksheet = workbook.add_worksheet()
        
        # ========== Format ==============
        header_table = workbook.add_format({'bold':True,'valign':'vcenter','align':'center','text_wrap':True})
        header_table.set_border()
        
        header_table_left = workbook.add_format({'bold':True,'valign':'vcenter','align':'left','text_wrap':True})
        header_table_left.set_border()

        body_table_left = workbook.add_format()
        body_table_left.set_align('left')
        body_table_left.set_align('vcenter')
        body_table_left.set_border()
        
        body_table_right = workbook.add_format()
        body_table_right.set_align('right')
        body_table_right.set_align('vcenter')
        body_table_right.set_border()
        body_table_right.set_num_format('#,##0')

        body_table_center = workbook.add_format()
        body_table_center.set_align('center')
        body_table_center.set_align('vcenter')
        body_table_center.set_border()

        body_table = workbook.add_format()
        body_table.set_align('right')
        body_table.set_align('vcenter')
        body_table.set_border()
        body_table.set_num_format('#,##0')

        body_table_des = workbook.add_format()
        body_table_des.set_align('right')
        body_table_des.set_align('vcenter')
        body_table_des.set_border()
        body_table_des.set_num_format('#,##0.#0')
        
        body_table_right_percent = workbook.add_format()
        body_table_right_percent.set_align('right')
        body_table_right_percent.set_align('vcenter')
        body_table_right_percent.set_border()
        body_table_right_percent.set_num_format('0%')
        
        body_table_right_normal = workbook.add_format()
        body_table_right_normal.set_align('right')
        body_table_right_normal.set_align('vcenter')
        body_table_right_normal.set_border()
        body_table_right_normal.set_num_format('0')

        worksheet.set_column('A:B', 20)
        worksheet.set_column('C:E', 30)
        worksheet.set_column('F:Z', 20)

        row = 0

        product = """
                SELECT tl.product_id, pp.default_code, pt.name from sales_user_target_line tl
                    LEFT JOIN product_product pp on pp.id = tl.product_id
                    LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
                    WHERE tl.month = '%s' and tl.year = '%s'
                GROUP BY tl.product_id, pp.default_code, pt.name
                ORDER BY tl.product_id
        """
        params = (self.bulan, self.tahun)
        self._cr.execute( product, params)
        product_results = self._cr.dictfetchall()
        
        user = """
                SELECT partner.name, tl.user_id from sales_user_target_line tl
                    LEFT JOIN res_users users on users.id = tl.user_id
                    LEFT JOIN res_partner partner on partner.id = users.partner_id
                        WHERE tl.month = '%s' and tl.year = '%s'
                GROUP BY tl.user_id, partner.name
                ORDER BY tl.user_id
        """
        self._cr.execute(user, params)
        user_results = self._cr.dictfetchall()

        worksheet.write(row, 1, 'I. TARGET', header_table_left)
        worksheet.write(row+1, 0, 'No.', header_table)
        worksheet.merge_range(row+1, 1, row+1, 2, 'NAMA PRODUK.', header_table)
        seq = 1
        
        col = 2
        for data in user_results:
            worksheet.write(row+1, col+1, data.get('name'), header_table)
            col += 1

        sum_product = len(product_results)
        sum_user = len(user_results)
        reset_col = 3
        first = False
        first_row_total1 = 0
        first_col_total1 = 0
        for data in product_results:
            worksheet.write(row+2, 0, seq, body_table_right)
            worksheet.write(row+2, 1, data.get('default_code'), body_table_left)
            worksheet.write(row+2, 2, data.get('name'), body_table_left)
            if not first:
                first_row_total1 = row + 2
                first_col_total1 = 3
            for user in user_results:
                new_param = (user.get('user_id'), data.get('product_id'))
                result = self.query_target_realisasi(new_param)
                new_result = result[0] if result else ''
                worksheet.write(row+2, reset_col, new_result.get('qty_target') if result else '', body_table_right)
                reset_col += 1
            row += 1
            seq += 1
            reset_col = 3
            first = True

        worksheet.write(row+2, 2, 'TOTAL', header_table)
        target_total = 0
        for user in user_results:
            col_row = xl_range(first_row_total1, first_col_total1, first_row_total1+sum_product-1, first_col_total1)
            worksheet.write_formula(row+2, first_col_total1, '=SUM(%s)' % col_row, body_table_right)
            if target_total == 0:
                target_total = row + 2
            first_col_total1 += 1

        row_sales = 2
        col_sales = 2
        sales = False
        
        row_realisasi = row + 3
        worksheet.write(row_realisasi, 1, 'II. REALISASI', header_table_left)
        seq = 1
        reset_col = 3
        first = False
        first_row_total2 = 0
        first_col_total2 = 0
        for data in product_results:
            worksheet.write(row_realisasi+1, 0, seq, body_table_right)
            worksheet.write(row_realisasi+1, 1, data.get('default_code'), body_table_left)
            worksheet.write(row_realisasi+1, 2, data.get('name'), body_table_left)
            if not first:
                first_row_total2 = row_realisasi + 1
                first_col_total2 = 3
            for user in user_results:
                new_param = (user.get('user_id'), data.get('product_id'))
                result = self.query_target_realisasi(new_param)
                new_result = result[0] if result else ''
                worksheet.write(row_realisasi+1, reset_col, new_result.get('qty_realisasi') if result else '', body_table_right)
                reset_col += 1
            row_realisasi += 1
            seq += 1
            reset_col = 3
            first = True
        worksheet.write(row_realisasi+1, 2, 'TOTAL', header_table)
        
        realisasi = 0
        for user in user_results:
            col_row = xl_range(first_row_total2, first_col_total2, first_row_total2+sum_product-1, first_col_total2)
            worksheet.write_formula(row_realisasi+1, first_col_total2, '=SUM(%s)' % col_row, body_table_right)
            if realisasi == 0:
                realisasi = row_realisasi+1
            first_col_total2 += 1

        worksheet.merge_range(row_realisasi+2, 1, row_realisasi+2, 2, 'III. PENCAPAIAN %', header_table_left)
        seq = 0
        for user in user_results:
            rowcol_1 = xl_rowcol_to_cell(target_total, first_col_total1-sum_user + seq)
            rowcol_2 = xl_rowcol_to_cell(realisasi, first_col_total2-sum_user + seq)
            worksheet.write_formula(row_realisasi+2, first_col_total2-sum_user +seq, '=%s/%s' % (rowcol_2, rowcol_1), body_table_right_percent)
            seq+= 1

        worksheet.merge_range(row_realisasi+3, 1, row_realisasi+3, 2, 'IV. BIAYA', header_table_left)
        first_col_biaya = 3
        for user in user_results:
            new_param = (user.get('user_id'),)
            result_biaya = self.query_biaya(new_param)
            worksheet.write(row_realisasi+3, first_col_biaya, result_biaya.get('biaya'), body_table_right)
            first_col_biaya+=1

        worksheet.merge_range(row_realisasi+4, 1, row_realisasi+4, 2, 'V. COST PER KARTON', header_table_left)
        first_cost_karton = 3
        seq = 0
        for user in user_results:
            rowcol_1 = xl_rowcol_to_cell(realisasi, first_cost_karton)
            rowcol_2 = xl_rowcol_to_cell(row_realisasi+3, first_cost_karton)
            worksheet.write_formula(row_realisasi+4, first_cost_karton, '=%s/%s' % (rowcol_2,rowcol_1), body_table_right_normal)
            first_cost_karton+=1
            seq =+1

        worksheet.merge_range(row_realisasi+5, 1, row_realisasi+5, 2, 'VI. LIMIT PIUTANG', header_table_left)
        first_col_limit = 3
        for user in user_results:
            new_param = (user.get('user_id'),)
            result_biaya = self.query_limit(new_param)
            worksheet.write(row_realisasi+5, first_col_limit, result_biaya.get('limit'), body_table_right)
            first_col_limit+=1
        
        worksheet.merge_range(row_realisasi+6, 1, row_realisasi+6, 2, 'VII. RASIO PIUTANG', header_table_left)

        workbook.close()
        out = base64.b64encode(fp.getvalue())
        fp.close()
        file_name = "report_a12.xlsx"
        return self.set_data_excel(out, file_name)

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