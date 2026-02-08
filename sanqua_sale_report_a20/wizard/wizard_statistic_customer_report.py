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

class StatisticCustomerReportWizard(models.TransientModel):
    _name = 'statistic.customer.report.wizard'
    _description = 'Statistic Customer Report'

    YEARS = [(str(num), str(num)) for num in range(2020, (datetime.now().year)+1 )]

    year = fields.Selection(YEARS, string='Periode',required=True)
    customer_ids = fields.Many2many('res.partner', string='Customer')
    name = fields.Char(string="Filename", readonly=True)
    data_file = fields.Binary(string="File", readonly=True)

    def fetch_data_piutang(self,partner_id):
        query = """
            SELECT am.partner_id, ct.name ,
            sum(am.amount_residual) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '01') AS januari,
            sum(am.amount_residual) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '02') AS februari,
            sum(am.amount_residual) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '03') AS maret,
            sum(am.amount_residual) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '04') AS april,
            sum(am.amount_residual) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '05') AS mei,
            sum(am.amount_residual) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '06') AS juni,
            sum(am.amount_residual) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '07') AS juli,
            sum(am.amount_residual) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '08') AS agustus,
            sum(am.amount_residual) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '09') AS september,
            sum(am.amount_residual) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '10') AS oktober,
            sum(am.amount_residual) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '11') AS november,
            sum(am.amount_residual) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '12') AS desember,
            SUM(am.amount_residual) FILTER (WHERE to_char(am.date,'YYYY') = %s)
            FROM account_move am
            JOIN crm_team ct ON ct.id = am.team_id
            WHERE am.partner_id = %s and am.state = 'posted' and am.company_id = %s
            group by am.partner_id,ct.name;
        """
        param = []
        for rec in range(0,13):
            param.append(self.year)
        param.append(partner_id)
        param.append(self.env.user.company_id.id)
        self._cr.execute(query, param)
        res = self._cr.dictfetchall()
        return res
        
    def fetch_data_umur_piutang(self, partner_id):
        query = """
            SELECT am.partner_id, ct.name, 
            sum((am.amount_residual / am.amount_total) * 30) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '01') AS januari,
            sum((am.amount_residual / am.amount_total) * 30) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '02') AS februari,
            sum((am.amount_residual / am.amount_total) * 30) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '03') AS maret,
            sum((am.amount_residual / am.amount_total) * 30) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '04') AS april,
            sum((am.amount_residual / am.amount_total) * 30) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '05') AS mei,
            sum((am.amount_residual / am.amount_total) * 30) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '06') AS juni,
            sum((am.amount_residual / am.amount_total) * 30) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '07') AS juli,
            sum((am.amount_residual / am.amount_total) * 30) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '08') AS agustus,
            sum((am.amount_residual / am.amount_total) * 30) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '09') AS september,
            sum((am.amount_residual / am.amount_total) * 30) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '10') AS oktober,
            sum((am.amount_residual / am.amount_total) * 30) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '11') AS november,
            sum((am.amount_residual / am.amount_total) * 30) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '12') AS desember,
            SUM((am.amount_residual / am.amount_total) * 30) FILTER (WHERE to_char(am.date,'YYYY') = %s)
            FROM account_move am
            JOIN crm_team ct ON ct.id = am.team_id
            WHERE am.partner_id = %s and am.state = 'posted' and am.company_id = %s
            group by am.partner_id,ct.name;
        """
        param = []
        for rec in range(0,13):
            param.append(self.year)
        param.append(partner_id)
        param.append(self.env.user.company_id.id)
        self._cr.execute(query, param)
        res = self._cr.dictfetchall()
        return res
        
    def fetch_data_rasio_piutang(self, partner_id):
        query = """
            SELECT am.partner_id, ct.name, 
            sum(am.amount_residual / am.amount_total * 100) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '01') AS januari,
            sum(am.amount_residual / am.amount_total * 100) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '02') AS februari,
            sum(am.amount_residual / am.amount_total * 100) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '03') AS maret,
            sum(am.amount_residual / am.amount_total * 100) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '04') AS april,
            sum(am.amount_residual / am.amount_total * 100) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '05') AS mei,
            sum(am.amount_residual / am.amount_total * 100) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '06') AS juni,
            sum(am.amount_residual / am.amount_total * 100) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '07') AS juli,
            sum(am.amount_residual / am.amount_total * 100) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '08') AS agustus,
            sum(am.amount_residual / am.amount_total * 100) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '09') AS september,
            sum(am.amount_residual / am.amount_total * 100) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '10') AS oktober,
            sum(am.amount_residual / am.amount_total * 100) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '11') AS november,
            sum(am.amount_residual / am.amount_total * 100) FILTER (WHERE to_char(am.date,'YYYY') = %s AND to_char(am.date,'MM') = '12') AS desember,
            SUM(am.amount_residual / am.amount_total * 100) FILTER (WHERE to_char(am.date,'YYYY') = %s)
            FROM account_move am
            JOIN crm_team ct ON ct.id = am.team_id
            WHERE am.partner_id = %s and am.state = 'posted' and am.company_id = %s
            group by am.partner_id,ct.name;
        """
        param = []
        for rec in range(0,13):
            param.append(self.year)
        param.append(partner_id)
        param.append(self.env.user.company_id.id)
        self._cr.execute(query, param)
        res = self._cr.dictfetchall()
        return res

    def fetch_data_credit_limit(self,partner_id):
        query = """
            SELECT ct.name as name, sum(credit_limit) as credit_limit
            FROM partner_pricelist pp
            JOIN crm_team ct ON pp.team_id = ct.id
			WHERE pp.partner_id = %s and ct.company_id = %s
            GROUP BY ct.name;
        """
        param = []
        param.append(partner_id)
        param.append(self.env.user.company_id.id)
        self._cr.execute(query, param)
        res = self._cr.dictfetchall()
        return res

    def fetch_data(self, partner_id, quantity=True):
        if quantity:
            query = """
                SELECT 
                    aml.partner_id,
	                aml.product_id,
                    pt.name,
                    pc.report_category,
                    sum(aml.quantity) FILTER (WHERE to_char(aml.date,'YYYY') = %s AND to_char(aml.date,'MM') = '01') AS januari,
                    sum(aml.quantity) FILTER (WHERE to_char(aml.date,'YYYY') = %s AND to_char(aml.date,'MM') = '02') AS februari,
                    sum(aml.quantity) FILTER (WHERE to_char(aml.date,'YYYY') = %s AND to_char(aml.date,'MM') = '03') AS maret,
                    sum(aml.quantity) FILTER (WHERE to_char(aml.date,'YYYY') = %s AND to_char(aml.date,'MM') = '04') AS april,
                    sum(aml.quantity) FILTER (WHERE to_char(aml.date,'YYYY') = %s AND to_char(aml.date,'MM') = '05') AS mei,
                    sum(aml.quantity) FILTER (WHERE to_char(aml.date,'YYYY') = %s AND to_char(aml.date,'MM') = '06') AS juni,
                    sum(aml.quantity) FILTER (WHERE to_char(aml.date,'YYYY') = %s AND to_char(aml.date,'MM') = '07') AS juli,
                    sum(aml.quantity) FILTER (WHERE to_char(aml.date,'YYYY') = %s AND to_char(aml.date,'MM') = '08') AS agustus,
                    sum(aml.quantity) FILTER (WHERE to_char(aml.date,'YYYY') = %s AND to_char(aml.date,'MM') = '09') AS september,
                    sum(aml.quantity) FILTER (WHERE to_char(aml.date,'YYYY') = %s AND to_char(aml.date,'MM') = '10') AS oktober,
                    sum(aml.quantity) FILTER (WHERE to_char(aml.date,'YYYY') = %s AND to_char(aml.date,'MM') = '11') AS november,
                    sum(aml.quantity) FILTER (WHERE to_char(aml.date,'YYYY') = %s AND to_char(aml.date,'MM') = '12') AS desember,
                    SUM(aml.quantity) FILTER (WHERE to_char(aml.date,'YYYY') = %s)
                FROM account_move_line aml
                JOIN product_product pp ON pp.id = aml.product_id
                JOIN product_template pt ON pt.id = pp.product_tmpl_id
                JOIN product_category pc ON pt.categ_id = pc.id
                WHERE aml.partner_id = %s and aml.company_id = %s and aml.exclude_from_invoice_tab = False and pc.report_category is not null
                GROUP BY aml.partner_id,aml.product_id,pt.name, pc.report_category
                ORDER BY pc.report_category DESC, aml.product_id;
            """
        else:
            query = """
                SELECT 
                    aml.partner_id,
	                aml.product_id,
                    pt.name,
                    pc.report_category,
                    sum(aml.price_total) FILTER (WHERE to_char(aml.date,'YYYY') = %s AND to_char(aml.date,'MM') = '01') AS januari,
                    sum(aml.price_total) FILTER (WHERE to_char(aml.date,'YYYY') = %s AND to_char(aml.date,'MM') = '02') AS februari,
                    sum(aml.price_total) FILTER (WHERE to_char(aml.date,'YYYY') = %s AND to_char(aml.date,'MM') = '03') AS maret,
                    sum(aml.price_total) FILTER (WHERE to_char(aml.date,'YYYY') = %s AND to_char(aml.date,'MM') = '04') AS april,
                    sum(aml.price_total) FILTER (WHERE to_char(aml.date,'YYYY') = %s AND to_char(aml.date,'MM') = '05') AS mei,
                    sum(aml.price_total) FILTER (WHERE to_char(aml.date,'YYYY') = %s AND to_char(aml.date,'MM') = '06') AS juni,
                    sum(aml.price_total) FILTER (WHERE to_char(aml.date,'YYYY') = %s AND to_char(aml.date,'MM') = '07') AS juli,
                    sum(aml.price_total) FILTER (WHERE to_char(aml.date,'YYYY') = %s AND to_char(aml.date,'MM') = '08') AS agustus,
                    sum(aml.price_total) FILTER (WHERE to_char(aml.date,'YYYY') = %s AND to_char(aml.date,'MM') = '09') AS september,
                    sum(aml.price_total) FILTER (WHERE to_char(aml.date,'YYYY') = %s AND to_char(aml.date,'MM') = '10') AS oktober,
                    sum(aml.price_total) FILTER (WHERE to_char(aml.date,'YYYY') = %s AND to_char(aml.date,'MM') = '11') AS november,
                    sum(aml.price_total) FILTER (WHERE to_char(aml.date,'YYYY') = %s AND to_char(aml.date,'MM') = '12') AS desember,
                    SUM(aml.price_total) FILTER (WHERE to_char(aml.date,'YYYY') = %s)
                FROM account_move_line aml
                JOIN product_product pp ON pp.id = aml.product_id
                JOIN product_template pt ON pt.id = pp.product_tmpl_id
                JOIN product_category pc ON pt.categ_id = pc.id
                WHERE aml.partner_id = %s and aml.company_id = %s and aml.exclude_from_invoice_tab = False and pc.report_category is not null
                GROUP BY aml.partner_id,aml.product_id,pt.name, pc.report_category
                ORDER BY pc.report_category DESC, aml.product_id;
            """
        param = []
        for rec in range(0,13):
            param.append(self.year)
        param.append(partner_id)
        param.append(self.env.user.company_id.id)
        self._cr.execute(query, param)
        res = self._cr.dictfetchall()
        return res

    def add_sheet(self, worksheet, workbook, partner_id):
        data = self.fetch_data(partner_id.id,quantity=True)
        nominal = self.fetch_data(partner_id.id,quantity=False)
        credit_limit = self.fetch_data_credit_limit(partner_id.id)
        piutang = self.fetch_data_piutang(partner_id.id)
        umur_piutang = self.fetch_data_umur_piutang(partner_id.id)
        rasio = self.fetch_data_rasio_piutang(partner_id.id)
        # ========= HEADER ==========
        header_format = workbook.add_format({'bold': True,'align':'center'})
        center_format = workbook.add_format({'align':'center'})
        center_format.set_num_format('#,##0')
        header_right_format = workbook.add_format({'bold': True,'align':'right'})
        header_right_format.set_num_format('#,##0')
        worksheet.set_column('A1:A1', 20)
        worksheet.set_column('B1:N1', 10)
        # ========== LIMIT ==========
        category = []
        for rec in data:
            if rec.get('report_category') not in category:
                category.append(rec.get('report_category'))
        row = 0
        for categ in category:
            if categ == 'sqa':
                limit = 0
                for lim in credit_limit:
                    if lim.get('name') == 'SQA':
                        limit = lim.get('credit_limit')
                worksheet.write(row, 0, "Limit SanQua", header_format)
                worksheet.write(row, 1, limit, header_right_format)
            if categ == 'btv':
                limit = 0
                for lim in credit_limit:
                    if lim.get('name') == 'BTV':
                        limit = lim.get('credit_limit')
                worksheet.write(row, 0, "Limit Batavia", header_format)
                worksheet.write(row, 1, limit, header_right_format)
            if categ == 'bvg':
                limit = 0
                for lim in credit_limit:
                    if lim.get('name') == 'BVG':
                        limit = lim.get('credit_limit')
                worksheet.write(row, 0, "Limit Beverage", header_format)
                worksheet.write(row, 1, limit, header_right_format)
            worksheet.write(row + 1, 0, "Type", header_format)
            worksheet.write(row + 1, 1, "Jan", header_format)
            worksheet.write(row + 1, 2, "Feb", header_format)
            worksheet.write(row + 1, 3, "March", header_format)
            worksheet.write(row + 1, 4, "Aprl", header_format)
            worksheet.write(row + 1, 5, "May", header_format)
            worksheet.write(row + 1, 6, "Jun", header_format)
            worksheet.write(row + 1, 7, "Jul", header_format)
            worksheet.write(row + 1, 8, "Aug", header_format)
            worksheet.write(row + 1, 9, "Sept", header_format)
            worksheet.write(row + 1, 10, "Oct", header_format)
            worksheet.write(row + 1, 11, "Nov", header_format)
            worksheet.write(row + 1, 12, "Dec", header_format)
            worksheet.write(row + 1, 13, "Total", header_format)

            row_idx = row + 2
            # ========= BODY ==========
            jan = 0
            feb = 0
            mar = 0
            apr = 0
            mei = 0
            jun = 0
            jul = 0
            ags = 0
            sept = 0
            okt = 0
            nov = 0
            des = 0
            total = 0
            for line in data:
                if line.get('partner_id') == partner_id.id and line.get('report_category') == categ:
                    worksheet.write(row_idx, 0, line.get('name'))
                    worksheet.write(row_idx, 1, line.get('januari') or '-',center_format)
                    worksheet.write(row_idx, 2, line.get('februari') or '-',center_format)
                    worksheet.write(row_idx, 3, line.get('maret') or '-',center_format)
                    worksheet.write(row_idx, 4, line.get('april') or '-',center_format)
                    worksheet.write(row_idx, 5, line.get('mei') or '-',center_format)
                    worksheet.write(row_idx, 6, line.get('juni') or '-',center_format)
                    worksheet.write(row_idx, 7, line.get('juli') or '-',center_format)
                    worksheet.write(row_idx, 8, line.get('agustus') or '-',center_format)
                    worksheet.write(row_idx, 9, line.get('september') or '-',center_format)
                    worksheet.write(row_idx, 10, line.get('oktober') or '-',center_format)
                    worksheet.write(row_idx, 11, line.get('november') or '-',center_format)
                    worksheet.write(row_idx, 12, line.get('desember') or '-',center_format)
                    worksheet.write(row_idx, 13, line.get('sum') or '-',center_format)
                    jan = jan + (line.get('januari') or 0.0)
                    feb = feb + (line.get('februari') or 0.0)
                    mar = mar + (line.get('maret') or 0.0)
                    apr = apr + (line.get('april') or 0.0)
                    mei = mei + (line.get('mei') or 0.0)
                    jun = jun + (line.get('juni') or 0.0)
                    jul = jul + (line.get('juli') or 0.0)
                    ags = ags + (line.get('agustus') or 0.0)
                    sept = sept + (line.get('september') or 0.0)
                    okt = okt + (line.get('oktober') or 0.0)
                    nov = nov + (line.get('november') or 0.0)
                    des = des + (line.get('desember') or 0.0)
                    total = total + (line.get('sum') or 0.0)
                    row_idx += 1
            worksheet.write(row_idx, 0, "Total", header_format)
            worksheet.write(row_idx, 1, jan or '-',center_format)
            worksheet.write(row_idx, 2, feb or '-',center_format)
            worksheet.write(row_idx, 3, mar or '-',center_format)
            worksheet.write(row_idx, 4, apr or '-',center_format)
            worksheet.write(row_idx, 5, mei or '-',center_format)
            worksheet.write(row_idx, 6, jun or '-',center_format)
            worksheet.write(row_idx, 7, jul or '-',center_format)
            worksheet.write(row_idx, 8, ags or '-',center_format)
            worksheet.write(row_idx, 9, sept or '-',center_format)
            worksheet.write(row_idx, 10, okt or '-',center_format)
            worksheet.write(row_idx, 11, nov or '-',center_format)
            worksheet.write(row_idx, 12, des or '-',center_format)
            worksheet.write(row_idx, 13, total or '-',center_format)
            row = row_idx + 2
        # ======= Nominal ============
        category = []
        for rec in nominal:
            if rec.get('report_category') not in category:
                category.append(rec.get('report_category'))
        for categ in category:
            if categ == 'sqa':
                worksheet.write(row, 0, "Nominal SanQua", header_format)
            if categ == 'btv':
                worksheet.write(row, 0, "Nominal Batavia", header_format)
            if categ == 'bvg':
                worksheet.write(row, 0, "Nominal Beverage", header_format)
            worksheet.write(row + 1, 0, "Type", header_format)
            worksheet.write(row + 1, 1, "Jan", header_format)
            worksheet.write(row + 1, 2, "Feb", header_format)
            worksheet.write(row + 1, 3, "March", header_format)
            worksheet.write(row + 1, 4, "Aprl", header_format)
            worksheet.write(row + 1, 5, "May", header_format)
            worksheet.write(row + 1, 6, "Jun", header_format)
            worksheet.write(row + 1, 7, "Jul", header_format)
            worksheet.write(row + 1, 8, "Aug", header_format)
            worksheet.write(row + 1, 9, "Sept", header_format)
            worksheet.write(row + 1, 10, "Oct", header_format)
            worksheet.write(row + 1, 11, "Nov", header_format)
            worksheet.write(row + 1, 12, "Dec", header_format)
            worksheet.write(row + 1, 13, "Total", header_format)

            row_idx = row + 2
            # ========= BODY ==========
            jan = 0
            feb = 0
            mar = 0
            apr = 0
            mei = 0
            jun = 0
            jul = 0
            ags = 0
            sept = 0
            okt = 0
            nov = 0
            des = 0
            total = 0
            for line in nominal:
                if line.get('partner_id') == partner_id.id and line.get('report_category') == categ:
                    worksheet.write(row_idx, 0, line.get('name'))
                    worksheet.write(row_idx, 1, line.get('januari') or '-',center_format)
                    worksheet.write(row_idx, 2, line.get('februari') or '-',center_format)
                    worksheet.write(row_idx, 3, line.get('maret') or '-',center_format)
                    worksheet.write(row_idx, 4, line.get('april') or '-',center_format)
                    worksheet.write(row_idx, 5, line.get('mei') or '-',center_format)
                    worksheet.write(row_idx, 6, line.get('juni') or '-',center_format)
                    worksheet.write(row_idx, 7, line.get('juli') or '-',center_format)
                    worksheet.write(row_idx, 8, line.get('agustus') or '-',center_format)
                    worksheet.write(row_idx, 9, line.get('september') or '-',center_format)
                    worksheet.write(row_idx, 10, line.get('oktober') or '-',center_format)
                    worksheet.write(row_idx, 11, line.get('november') or '-',center_format)
                    worksheet.write(row_idx, 12, line.get('desember') or '-',center_format)
                    worksheet.write(row_idx, 13, line.get('sum') or '-',center_format)
                    jan = jan + (line.get('januari') or 0.0)
                    feb = feb + (line.get('februari') or 0.0)
                    mar = mar + (line.get('maret') or 0.0)
                    apr = apr + (line.get('april') or 0.0)
                    mei = mei + (line.get('mei') or 0.0)
                    jun = jun + (line.get('juni') or 0.0)
                    jul = jul + (line.get('juli') or 0.0)
                    ags = ags + (line.get('agustus') or 0.0)
                    sept = sept + (line.get('september') or 0.0)
                    okt = okt + (line.get('oktober') or 0.0)
                    nov = nov + (line.get('november') or 0.0)
                    des = des + (line.get('desember') or 0.0)
                    total = total + (line.get('sum') or 0.0)
                    row_idx += 1
            worksheet.write(row_idx, 0, "Total", header_format)
            worksheet.write(row_idx, 1, jan or '-',center_format)
            worksheet.write(row_idx, 2, feb or '-',center_format)
            worksheet.write(row_idx, 3, mar or '-',center_format)
            worksheet.write(row_idx, 4, apr or '-',center_format)
            worksheet.write(row_idx, 5, mei or '-',center_format)
            worksheet.write(row_idx, 6, jun or '-',center_format)
            worksheet.write(row_idx, 7, jul or '-',center_format)
            worksheet.write(row_idx, 8, ags or '-',center_format)
            worksheet.write(row_idx, 9, sept or '-',center_format)
            worksheet.write(row_idx, 10, okt or '-',center_format)
            worksheet.write(row_idx, 11, nov or '-',center_format)
            worksheet.write(row_idx, 12, des or '-',center_format)
            worksheet.write(row_idx, 13, total or '-',center_format)
            row = row_idx + 2
        # ======= Piutang =========
        worksheet.write(row, 0, "Piutang", header_format)
        worksheet.write(row + 1, 0, "Divisi", header_format)
        worksheet.write(row + 1, 1, "Jan", header_format)
        worksheet.write(row + 1, 2, "Feb", header_format)
        worksheet.write(row + 1, 3, "March", header_format)
        worksheet.write(row + 1, 4, "Aprl", header_format)
        worksheet.write(row + 1, 5, "May", header_format)
        worksheet.write(row + 1, 6, "Jun", header_format)
        worksheet.write(row + 1, 7, "Jul", header_format)
        worksheet.write(row + 1, 8, "Aug", header_format)
        worksheet.write(row + 1, 9, "Sept", header_format)
        worksheet.write(row + 1, 10, "Oct", header_format)
        worksheet.write(row + 1, 11, "Nov", header_format)
        worksheet.write(row + 1, 12, "Dec", header_format)
        worksheet.write(row + 1, 13, "Total", header_format)

        row_idx = row + 2
        # ========= BODY ==========
        jan = 0
        feb = 0
        mar = 0
        apr = 0
        mei = 0
        jun = 0
        jul = 0
        ags = 0
        sept = 0
        okt = 0
        nov = 0
        des = 0
        total = 0
        for line in piutang:
            if line.get('partner_id') == partner_id.id and line.get('name') == categ.upper():
                worksheet.write(row_idx, 0, line.get('name'))
                worksheet.write(row_idx, 1, line.get('januari') or '-',center_format)
                worksheet.write(row_idx, 2, line.get('februari') or '-',center_format)
                worksheet.write(row_idx, 3, line.get('maret') or '-',center_format)
                worksheet.write(row_idx, 4, line.get('april') or '-',center_format)
                worksheet.write(row_idx, 5, line.get('mei') or '-',center_format)
                worksheet.write(row_idx, 6, line.get('juni') or '-',center_format)
                worksheet.write(row_idx, 7, line.get('juli') or '-',center_format)
                worksheet.write(row_idx, 8, line.get('agustus') or '-',center_format)
                worksheet.write(row_idx, 9, line.get('september') or '-',center_format)
                worksheet.write(row_idx, 10, line.get('oktober') or '-',center_format)
                worksheet.write(row_idx, 11, line.get('november') or '-',center_format)
                worksheet.write(row_idx, 12, line.get('desember') or '-',center_format)
                worksheet.write(row_idx, 13, line.get('sum') or '-',center_format)
                jan = jan + (line.get('januari') or 0.0)
                feb = feb + (line.get('februari') or 0.0)
                mar = mar + (line.get('maret') or 0.0)
                apr = apr + (line.get('april') or 0.0)
                mei = mei + (line.get('mei') or 0.0)
                jun = jun + (line.get('juni') or 0.0)
                jul = jul + (line.get('juli') or 0.0)
                ags = ags + (line.get('agustus') or 0.0)
                sept = sept + (line.get('september') or 0.0)
                okt = okt + (line.get('oktober') or 0.0)
                nov = nov + (line.get('november') or 0.0)
                des = des + (line.get('desember') or 0.0)
                total = total + (line.get('sum') or 0.0)
                row_idx += 1
        worksheet.write(row_idx, 0, "Total", header_format)
        worksheet.write(row_idx, 1, jan or '-',center_format)
        worksheet.write(row_idx, 2, feb or '-',center_format)
        worksheet.write(row_idx, 3, mar or '-',center_format)
        worksheet.write(row_idx, 4, apr or '-',center_format)
        worksheet.write(row_idx, 5, mei or '-',center_format)
        worksheet.write(row_idx, 6, jun or '-',center_format)
        worksheet.write(row_idx, 7, jul or '-',center_format)
        worksheet.write(row_idx, 8, ags or '-',center_format)
        worksheet.write(row_idx, 9, sept or '-',center_format)
        worksheet.write(row_idx, 10, okt or '-',center_format)
        worksheet.write(row_idx, 11, nov or '-',center_format)
        worksheet.write(row_idx, 12, des or '-',center_format)
        worksheet.write(row_idx, 13, total or '-',center_format)
        row = row_idx + 2
        # ======= Umur Piutang =========
        worksheet.write(row, 0, "Umur Piutang", header_format)
        worksheet.write(row + 1, 0, "Divisi", header_format)
        worksheet.write(row + 1, 1, "Jan", header_format)
        worksheet.write(row + 1, 2, "Feb", header_format)
        worksheet.write(row + 1, 3, "March", header_format)
        worksheet.write(row + 1, 4, "Aprl", header_format)
        worksheet.write(row + 1, 5, "May", header_format)
        worksheet.write(row + 1, 6, "Jun", header_format)
        worksheet.write(row + 1, 7, "Jul", header_format)
        worksheet.write(row + 1, 8, "Aug", header_format)
        worksheet.write(row + 1, 9, "Sept", header_format)
        worksheet.write(row + 1, 10, "Oct", header_format)
        worksheet.write(row + 1, 11, "Nov", header_format)
        worksheet.write(row + 1, 12, "Dec", header_format)
        worksheet.write(row + 1, 13, "Total", header_format)

        row_idx = row + 2
        # ========= BODY ==========
        jan = 0
        feb = 0
        mar = 0
        apr = 0
        mei = 0
        jun = 0
        jul = 0
        ags = 0
        sept = 0
        okt = 0
        nov = 0
        des = 0
        total = 0
        for line in umur_piutang:
            if line.get('partner_id') == partner_id.id and line.get('name') == categ.upper():
                worksheet.write(row_idx, 0, line.get('name'))
                worksheet.write(row_idx, 1, line.get('januari') or '-',center_format)
                worksheet.write(row_idx, 2, line.get('februari') or '-',center_format)
                worksheet.write(row_idx, 3, line.get('maret') or '-',center_format)
                worksheet.write(row_idx, 4, line.get('april') or '-',center_format)
                worksheet.write(row_idx, 5, line.get('mei') or '-',center_format)
                worksheet.write(row_idx, 6, line.get('juni') or '-',center_format)
                worksheet.write(row_idx, 7, line.get('juli') or '-',center_format)
                worksheet.write(row_idx, 8, line.get('agustus') or '-',center_format)
                worksheet.write(row_idx, 9, line.get('september') or '-',center_format)
                worksheet.write(row_idx, 10, line.get('oktober') or '-',center_format)
                worksheet.write(row_idx, 11, line.get('november') or '-',center_format)
                worksheet.write(row_idx, 12, line.get('desember') or '-',center_format)
                worksheet.write(row_idx, 13, line.get('sum') or '-',center_format)
                jan = jan + (line.get('januari') or 0.0)
                feb = feb + (line.get('februari') or 0.0)
                mar = mar + (line.get('maret') or 0.0)
                apr = apr + (line.get('april') or 0.0)
                mei = mei + (line.get('mei') or 0.0)
                jun = jun + (line.get('juni') or 0.0)
                jul = jul + (line.get('juli') or 0.0)
                ags = ags + (line.get('agustus') or 0.0)
                sept = sept + (line.get('september') or 0.0)
                okt = okt + (line.get('oktober') or 0.0)
                nov = nov + (line.get('november') or 0.0)
                des = des + (line.get('desember') or 0.0)
                total = total + (line.get('sum') or 0.0)
                row_idx += 1
        worksheet.write(row_idx, 0, "Total", header_format)
        worksheet.write(row_idx, 1, jan or '-',center_format)
        worksheet.write(row_idx, 2, feb or '-',center_format)
        worksheet.write(row_idx, 3, mar or '-',center_format)
        worksheet.write(row_idx, 4, apr or '-',center_format)
        worksheet.write(row_idx, 5, mei or '-',center_format)
        worksheet.write(row_idx, 6, jun or '-',center_format)
        worksheet.write(row_idx, 7, jul or '-',center_format)
        worksheet.write(row_idx, 8, ags or '-',center_format)
        worksheet.write(row_idx, 9, sept or '-',center_format)
        worksheet.write(row_idx, 10, okt or '-',center_format)
        worksheet.write(row_idx, 11, nov or '-',center_format)
        worksheet.write(row_idx, 12, des or '-',center_format)
        worksheet.write(row_idx, 13, total or '-',center_format)
        row = row_idx + 2
        # ======= Rasio =========
        worksheet.write(row, 0, "Rasio", header_format)
        worksheet.write(row + 1, 0, "Divisi", header_format)
        worksheet.write(row + 1, 1, "Jan", header_format)
        worksheet.write(row + 1, 2, "Feb", header_format)
        worksheet.write(row + 1, 3, "March", header_format)
        worksheet.write(row + 1, 4, "Aprl", header_format)
        worksheet.write(row + 1, 5, "May", header_format)
        worksheet.write(row + 1, 6, "Jun", header_format)
        worksheet.write(row + 1, 7, "Jul", header_format)
        worksheet.write(row + 1, 8, "Aug", header_format)
        worksheet.write(row + 1, 9, "Sept", header_format)
        worksheet.write(row + 1, 10, "Oct", header_format)
        worksheet.write(row + 1, 11, "Nov", header_format)
        worksheet.write(row + 1, 12, "Dec", header_format)
        worksheet.write(row + 1, 13, "Total", header_format)

        row_idx = row + 2
        # ========= BODY ==========
        jan = 0
        feb = 0
        mar = 0
        apr = 0
        mei = 0
        jun = 0
        jul = 0
        ags = 0
        sept = 0
        okt = 0
        nov = 0
        des = 0
        total = 0
        for line in rasio:
            if line.get('partner_id') == partner_id.id and line.get('name') == categ.upper():
                worksheet.write(row_idx, 0, line.get('name'))
                worksheet.write(row_idx, 1, line.get('januari') or '-',center_format)
                worksheet.write(row_idx, 2, line.get('februari') or '-',center_format)
                worksheet.write(row_idx, 3, line.get('maret') or '-',center_format)
                worksheet.write(row_idx, 4, line.get('april') or '-',center_format)
                worksheet.write(row_idx, 5, line.get('mei') or '-',center_format)
                worksheet.write(row_idx, 6, line.get('juni') or '-',center_format)
                worksheet.write(row_idx, 7, line.get('juli') or '-',center_format)
                worksheet.write(row_idx, 8, line.get('agustus') or '-',center_format)
                worksheet.write(row_idx, 9, line.get('september') or '-',center_format)
                worksheet.write(row_idx, 10, line.get('oktober') or '-',center_format)
                worksheet.write(row_idx, 11, line.get('november') or '-',center_format)
                worksheet.write(row_idx, 12, line.get('desember') or '-',center_format)
                worksheet.write(row_idx, 13, line.get('sum') or '-',center_format)
                jan = jan + (line.get('januari') or 0.0)
                feb = feb + (line.get('februari') or 0.0)
                mar = mar + (line.get('maret') or 0.0)
                apr = apr + (line.get('april') or 0.0)
                mei = mei + (line.get('mei') or 0.0)
                jun = jun + (line.get('juni') or 0.0)
                jul = jul + (line.get('juli') or 0.0)
                ags = ags + (line.get('agustus') or 0.0)
                sept = sept + (line.get('september') or 0.0)
                okt = okt + (line.get('oktober') or 0.0)
                nov = nov + (line.get('november') or 0.0)
                des = des + (line.get('desember') or 0.0)
                total = total + (line.get('sum') or 0.0)
                row_idx += 1
        worksheet.write(row_idx, 0, "Total", header_format)
        worksheet.write(row_idx, 1, jan or '-',center_format)
        worksheet.write(row_idx, 2, feb or '-',center_format)
        worksheet.write(row_idx, 3, mar or '-',center_format)
        worksheet.write(row_idx, 4, apr or '-',center_format)
        worksheet.write(row_idx, 5, mei or '-',center_format)
        worksheet.write(row_idx, 6, jun or '-',center_format)
        worksheet.write(row_idx, 7, jul or '-',center_format)
        worksheet.write(row_idx, 8, ags or '-',center_format)
        worksheet.write(row_idx, 9, sept or '-',center_format)
        worksheet.write(row_idx, 10, okt or '-',center_format)
        worksheet.write(row_idx, 11, nov or '-',center_format)
        worksheet.write(row_idx, 12, des or '-',center_format)
        worksheet.write(row_idx, 13, total or '-',center_format)
        row = row_idx + 2



    def generate_excel(self):
        """ Generate excel. """
        self.ensure_one()
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        for rec in self.customer_ids:
            worksheet = workbook.add_worksheet(rec.name)
            self.add_sheet(worksheet, workbook, rec)

        workbook.close()
        out = base64.b64encode(fp.getvalue())
        fp.close()
        filename = ('statistic_customer_%s.xlsx') % (datetime.now().year)
        if len(self.customer_ids) == 1 :
            filename = ('statistic_customer_%s.xlsx') % (self.customer_ids.display_name)
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

    