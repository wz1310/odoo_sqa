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


class WizardMisA9Report(models.Model):
    _name = 'wizard.mis.a9.report'
    _description = 'Wizard Mis a9 Report'

    customer_ids = fields.Many2many('res.partner',string='Customer')
    name = fields.Char(string="Filename", readonly=True)
    data_file = fields.Binary(string="File", readonly=True)

    def btn_confirm(self):
        data = self._get_data_A9()
        return self.generate_excel(data)

    def _get_data_A9(self):
        customer_filter = ""
        m_comp = ""
        if self.customer_ids:
            if len(self.customer_ids) == 1:
                customer_tuple = "(%s)" % self.customer_ids.id
            else:
                customer_tuple = tuple(self.customer_ids.ids)
            customer_filter = (" a.partner_id IN %s") % (str(customer_tuple))
        else:
            customer_filter = (" a.partner_id IN (a.partner_id)")
        if len(tuple(self.env.context['allowed_company_ids']))>1:
            m_comp = "AND so.company_id in %s" % str(tuple(self.env.context['allowed_company_ids']))
        else:
            m_comp = "AND so.company_id = %s" % str(self.env.company.id)
        query = """
        -- SISA SO BLM RELEASE (STATUS: AKTIF) + SJ BLM INVOICE + INVOICE BLM BAYAR
        -- 1. SO AKTIF BLM RELEASE
        WITH so_active_not_release_yet AS (
        SELECT so.partner_id, so.name AS "so_no", pp.id AS "product_id", pt.name AS "product_name", sol.product_uom_qty AS "qty_so", sol.qty_delivered, (sol.product_uom_qty - sol.qty_delivered) AS "remaining_qty", 
        ((sol.price_unit - sol.discount_fixed_line) * (sol.product_uom_qty - sol.qty_delivered)) AS "current_credit"
        FROM sale_order so LEFT JOIN sale_order_line sol ON so.id = sol.order_id
        LEFT JOIN product_product pp ON pp.id = sol.product_id
        LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
        WHERE so.state = 'sale' """+m_comp+"""
        AND so.validity_date > CURRENT_DATE
        AND sol.price_unit <> 0
        ORDER BY product_id, ((sol.price_unit - sol.discount_fixed_line) * (sol.product_uom_qty - sol.qty_delivered)) DESC
        ),
        -- 2. SJ BLM INVOICE
        sj_not_invoice_yet AS (
        SELECT so.partner_id,so.name AS "so_no", sp.doc_name AS "sj_no",pp.id AS "product_id",pt.name AS "product_name", sm.product_uom_qty, coalesce(sm_return.product_uom_qty, 0) AS "qty_return",
        (sm.product_uom_qty - coalesce(sm_return.product_uom_qty, 0) ) AS "qty_net",
        (
        (sm.product_uom_qty - coalesce(sm_return.product_uom_qty, 0) ) * (sol.price_unit - coalesce(sol.discount_fixed_line,0))
        ) AS "current_credit"
        FROM stock_picking sp LEFT JOIN sale_order so ON sp.sale_id = so.id
        LEFT JOIN sale_order_line sol ON so.id = sol.order_id
        LEFT JOIN stock_move sm ON (sm.picking_id = sp.id AND sol.product_id = sm.product_id)
        LEFT JOIN product_product pp ON ( pp.id = sm.product_id)
        LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
        LEFT JOIN stock_move sm_return ON ( sm.id = sm_return.origin_returned_move_id AND sm_return.state = 'done' ) 
        LEFT JOIN stock_picking_type AS spt ON sp.picking_type_id = spt.id
        WHERE sol.price_unit <> 0
        AND sp.invoice_id IS NULL
        AND spt.code IN ('outgoing') AND sp.state != 'cancel'
        AND sp.company_id = 2
        AND sp.location_dest_id = 5
        AND sp.doc_name <> 'New'
        AND sm.name not ilike 'Free %'
        ),
        invoice_not_pay_yet AS (
        -- 3. INVOICE BLM BAYAR
        SELECT id, partner_id,team_id, name, amount_residual_signed AS "current_credit"
        FROM account_move am 
        WHERE company_id = 2    
        AND type = 'out_invoice'
        AND amount_residual_signed <> 0
        AND state = 'posted'
        ORDER BY team_id 
        ),
        product_division AS (
        SELECT pp.id, ct.id AS "division_id", ct.name AS "division_name", pc.name AS "category_name", pt.name AS "product_name"
        FROM crm_team ct LEFT JOIN crm_team_product_category_rel ctpc ON ct.id = ctpc.crm_team_id
        LEFT JOIN product_category pc ON pc.id = ctpc.product_category_id
        LEFT JOIN product_template pt ON pt.categ_id = pc.id
        LEFT JOIN product_product pp ON pp.product_tmpl_id = pt.id          
        WHERE ct.company_id = 2
        AND ct.state = 'done'
        ),
        division AS (
        SELECT ct.id AS "division_id", ct.name AS "division_name"
        FROM crm_team ct
        WHERE ct.company_id = 2
        AND ct.state = 'done'
        ),
        partner_division AS (
        SELECT rp.id AS "partner_id", pp.team_id, rc.name AS "company_name", rp.name AS "customer_name", rp.code AS "customer_code", rp_sales.name AS "sales_name", rp_sales_admin.name AS "sales_admin_name",  apt.name AS "payment_term_name", pp.credit_limit
        FROM partner_pricelist pp LEFT JOIN res_company rc ON pp.company_id = rc.id
        LEFT JOIN res_partner rp ON rp.id = pp.partner_id
        LEFT JOIN res_users ru ON ru.id = pp.user_id 
        LEFT JOIN res_partner rp_sales ON rp_sales.id = ru.partner_id
        LEFT JOIN res_users ru_sa ON ru_sa.id = pp.sales_admin_id
        LEFT JOIN res_partner rp_sales_admin ON rp_sales_admin.id = ru_sa.partner_id
        LEFT JOIN account_payment_term apt ON apt.id = pp.payment_term_id
        )
        SELECT b.company_name, b.customer_code, b.customer_name, b.sales_name, b.sales_admin_name, b.payment_term_name, b.credit_limit,
        b.division_id, b.division_name, SUM(b."SO Amount") AS "SO Amount", SUM(b."SJ Amount") AS "SJ Amount", SUM(b."Invoice Amount") AS "Invoice Amount"
        FROM (
        SELECT pd.company_name, pd.customer_code, pd.customer_name, pd.sales_name, pd.sales_admin_name, pd.payment_term_name, pd.credit_limit,
        a.division_id, a.division_name, 
        CASE WHEN a."Category" ilike 'Sisa SO masih aktif' THEN SUM(a.current_credit) ELSE 0 END AS "SO Amount",
        CASE WHEN a."Category" ilike 'SJ yang blm invoice' THEN SUM(a.current_credit) ELSE 0 END AS "SJ Amount",
        CASE WHEN a."Category" ilike 'Invoice belum terbayar' THEN SUM(a.current_credit) ELSE 0 END AS "Invoice Amount"
        FROM (
        SELECT a.partner_id,'Sisa SO masih aktif' AS "Category",pd.division_id, pd.division_name, SUM(a.current_credit) AS "current_credit"
        FROM so_active_not_release_yet a LEFT JOIN product_division pd ON a.product_id = pd.id
        WHERE """+customer_filter+"""
        GROUP BY a.partner_id, pd.division_id, pd.division_name
        UNION
        SELECT a.partner_id,'SJ yang blm invoice' AS "Category", pd.division_id,pd.division_name, SUM(a.current_credit) AS "current_credit"
        FROM sj_not_invoice_yet a LEFT JOIN product_division pd ON a.product_id = pd.id
        WHERE """+customer_filter+""" 
        GROUP BY a.partner_id, pd.division_id, pd.division_name
        UNION
        SELECT a.partner_id,'Invoice belum terbayar' AS "Category",d.division_id,d.division_name, SUM(a.current_credit) AS "current_credit"
        FROM invoice_not_pay_yet a LEFT JOIN division d ON a.team_id = d.division_id
        WHERE """+customer_filter+"""  
        GROUP BY a.partner_id, d.division_id, d.division_name
        ) a LEFT JOIN partner_division pd ON ( a.division_id = pd.team_id AND a.partner_id = pd.partner_id)
        WHERE a.division_id IS NOT NULL
        GROUP BY a."Category",pd.company_name, pd.customer_code, pd.customer_name, pd.sales_name, pd.sales_admin_name, pd.payment_term_name, pd.credit_limit,a.division_id, a.division_name
        ) b
        GROUP BY b.company_name, b.customer_code, b.customer_name, b.sales_name, b.sales_admin_name, b.payment_term_name, b.credit_limit,
        b.division_id, b.division_name"""
        self.env.cr.execute(query)
        query_res = self.env.cr.fetchall()
        return query_res

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
        mb_center_style = workbook.add_format({'bold': 1, 'valign':'vcenter',
            'font_name':'Arial', 'font_size':16})
        mb_center_style.set_text_wrap()
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
        worksheet.merge_range('A1:E2','Report Limit Credit',mb_center_style)
        worksheet.write(3, 0, "Company",bolder_style)
        worksheet.write(3, 1, "Kode Customer",bolder_style)
        worksheet.write(3, 2, "Customer",bolder_style)
        worksheet.write(3, 3, "Divisi",bolder_style)
        worksheet.write(3, 4, "Nama Sales",bolder_style)
        worksheet.write(3, 5, "Nama Sales Admin",bolder_style)
        worksheet.write(3, 6, "TOP",bolder_style)
        worksheet.write(3, 7, "Credit Limit",bolder_style)
        worksheet.write(3, 8, "SO Amount",bolder_style)
        worksheet.write(3, 9, "SJ Amount",bolder_style)
        worksheet.write(3, 10, "Invoice Amount",bolder_style)
        worksheet.write(3, 11, "Total",bolder_style)
        worksheet.write(3, 12, "Spare",bolder_style)
        # worksheet.write(3, 14, "Kendala Pengiriman",bolder_style)
        # =============== HEADER ===============

        # =============== BODY ===============
        format_right = workbook.add_format({'align': 'right'})

        row_idx = 4
        for line in data:
            credit = line[6] or 0.0
            so_am = line[9] or 0.0 
            sj_am = line[10] or 0.0 
            inv_am = line[11] or 0.0 
            total = so_am+sj_am+inv_am
            spare = credit - total
            # spare = sum(str(line[6] - total))
            worksheet.write(row_idx, 0, line[0], normal_style)
            worksheet.write(row_idx, 1, line[1], normal_style)
            worksheet.write(row_idx, 2, line[2], normal_style)
            worksheet.write(row_idx, 3, line[8], normal_style)
            worksheet.write(row_idx, 4, line[3], normal_style)
            worksheet.write(row_idx, 5, line[4], normal_style)
            worksheet.write(row_idx, 6, line[5], normal_style)
            worksheet.write(row_idx, 7, line[6], normal_style)
            worksheet.write(row_idx, 8, line[9], normal_style)
            worksheet.write(row_idx, 9, line[10], normal_style)
            worksheet.write(row_idx, 10, line[11], normal_style)
            worksheet.write(row_idx, 11, total, normal_style)
            worksheet.write(row_idx, 12, spare, normal_style)
            row_idx += 1
        # =============== BODY ===============

        workbook.close()
        out = base64.b64encode(fp.getvalue())
        fp.close()
        filename = 'report_limit_credit_A9.xlsx'
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
            'url': '/web/content?model=wizard.mis.a9.report&field=data_file&filename_field=name&id=%s&download=true&filename=%s' %(self.id, filename,),
        }
