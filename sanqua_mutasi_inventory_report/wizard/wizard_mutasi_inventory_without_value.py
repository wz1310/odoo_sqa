# -*- coding: utf-8 -*-
import base64
import io
import xlsxwriter
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning
from pytz import timezone, UTC

class StockLastView(models.TransientModel):
    _name = "stock.last.view.value"
    _description = "Stock Last View"
    _order = "date"

    date = fields.Datetime()
    product_id = fields.Many2one(comodel_name="product.product")
    product_qty = fields.Float()
    product_uom_qty = fields.Float()
    product_uom = fields.Many2one(comodel_name="uom.uom")
    reference = fields.Char()
    location_id = fields.Many2one(comodel_name="stock.location")
    location_dest_id = fields.Many2one(comodel_name="stock.location")
    is_initial = fields.Boolean()
    product_in = fields.Float()
    product_out = fields.Float()
    order = fields.Char()
    description = fields.Char()
    price = fields.Float()
    price_in = fields.Float()
    price_out = fields.Float()
    name = fields.Char()
    code = fields.Char()
    tipe = fields.Char()
    product_price_in = fields.Float()
    product_price_out = fields.Float()
    product_total_in = fields.Float()
    product_total_out = fields.Float()
    balance = fields.Float()
    code_product = fields.Char()
    product_name = fields.Char()
    company_id = fields.Many2one(comodel_name="res.company")

class WizardMutasiInventoryReport(models.TransientModel):
    _name = 'wizard.mutasi.inventory.report.value'
    _description = 'Form wizard to generate mutasi inventory report'
    
    name = fields.Char('Filename', readonly=True)
    data = fields.Binary('File', readonly=True)
    product_classification = fields.Selection([('bahanbaku','Bahan Baku'),
                                               ('barangsetengahjadi','Barang 1/2 Jadi'),
                                               ('barangjadi','Barang Jadi'),
                                               ('sparepart','Sparepart'),
                                               ('bahankimia','Bahan Kimia'),
                                               ('lainlain','Lain-Lain')],'Product Classification')
    product_classification_ids = fields.Many2many('master.classification.product.value', 'prod_class_id', 'wiz_mutasi_id')
    company_id = fields.Many2one('res.company',
								 string='Company',
								 required=True, default=lambda self: self.env.company)
    state = fields.Selection([('choose','choose'),('get','get')], default='choose')

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    results = fields.Many2many(
        comodel_name="stock.last.view.value",
        compute="_compute_results",
        help="Use compute fields, so there is nothing store in database",
    )
    result_query2 = fields.Many2many(
        comodel_name="stock.last.view.value",
        compute="_compute_results_stock",
        help="Use compute fields, so there is nothing store in database",
    )
    

    def _compute_results(self):
        self.ensure_one()
        locations = self.env["stock.location"]
        date_from = self.start_date
        date_to = self.end_date
        product_tmpl_ids = self.env['product.template'].search([('product_classification', 'in', ('barangjadi','barangsetengahjadi'))])
        product_ids = self.env['product.product'].search([('product_tmpl_id', 'in', product_tmpl_ids.ids)])
        account_ids = product_ids.mapped('categ_id.property_stock_valuation_account_id').ids
        query2 = """
            SELECT am.date, sm.product_id, sm.product_qty, sm.product_uom_qty, sm.product_uom, 
                CASE WHEN sm.origin_returned_move_id IS NOT NULL then sp.name 
                    WHEN sm.picking_id IS NOT NULL then sp.name
                    WHEN sm.inventory_id IS NOT NULL then si.name
                    WHEN sm.production_id IS NOT NULL then mp.name
                    else TRIM(REPLACE(REPLACE(aml.name, pt.name, ''),'-','')) END as order, 
                pt.name, spt.code, aa.name,
                CASE WHEN sm.origin_returned_move_id IS NOT NULL and spt.code = 'incoming' and sm.purchase_line_id IS NOT NULL then 'Retur to Return Pembelian' 
                    WHEN sm.origin_returned_move_id IS NOT NULL and spt.code = 'outgoing' and sm.purchase_line_id IS NULL then 'Retur to Retur Penjualan'
                    WHEN sm.origin_returned_move_id IS NOT NULL and spt.code = 'incoming' then 'Retur Penjualan' 
                    WHEN sm.origin_returned_move_id IS NOT NULL and spt.code = 'outgoing' then 'Retur Pembelian'
                    WHEN sm.origin_returned_move_id IS NULL and spt.code = 'incoming' then 'Receipt'
                    WHEN sm.origin_returned_move_id IS NULL and spt.code = 'outgoing' then 'Delivery Order'
                    WHEN sm.inventory_id IS NOT NULL then 'Stock Adjustment'
                    WHEN sm.production_id IS NOT NULL then 'Manufacture'
                    WHEN sm.raw_material_production_id IS NOT NULL then 'Raw Material'
                    WHEN aml.name LIKE %s then 'Scrap'
                    WHEN sm.picking_id IS NULL then 'Adjustment from Product'
                    WHEN sm.scrapped IS TRUE then 'Scrap from IT'
                    else '' END as tipe,
                sm.price_unit as price,
                CASE WHEN aml.quantity > 0.0 then aml.quantity else 0.0 END as product_in,
                CASE WHEN aml.quantity > 0.0 then abs(round(aml.debit / aml.quantity, 2)) else 0.0 END as product_price_in,
                CASE WHEN aml.quantity > 0.0 then aml.debit else 0.0 END as product_total_in,
                CASE WHEN aml.quantity < 0.0 then abs(aml.quantity) else 0.0 END as product_out,
                CASE WHEN aml.quantity < 0.0 then abs(round(aml.credit / aml.quantity, 2)) else 0.0 END as product_price_out,
                CASE WHEN aml.quantity < 0.0 then abs(aml.credit) else 0.0 END as product_total_out,
                CASE WHEN sm.date <= %s then True else True end as is_initial,
                aml.balance,
                pt.name as product_name,
                pp.default_code as code_product,
                sm.company_id as company_id
                    from account_move_line aml
                left join account_move am ON aml.move_id = am.id
                left join stock_move sm ON am.stock_move_id = sm.id
                left join stock_picking sp ON sm.picking_id = sp.id
                left join stock_picking_type spt ON sp.picking_type_id = spt.id
                left join product_product pp ON sm.product_id = pp.id
                left join product_template pt ON pp.product_tmpl_id = pt.id
                left join account_account aa ON aml.account_id = aa.id
                left join stock_inventory si ON	sm.inventory_id = si.id
                left join mrp_production mp ON sm.production_id = mp.id
                where 
                    aa.id in %s
                    and pt.product_classification in ('barangjadi', 'barangsetengahjadi')
                    and CAST(am.date AS date) <= %s
                    and CAST(am.date AS date) >= %s
                order by am.date, am.id
        """
        #new
        self._cr.execute(
            query2,
            ('%Scrap%',
                date_to,
                tuple(account_ids),
                date_to,
                date_from
            ),
        )
        
        stock_card_results = self._cr.dictfetchall()
        ReportLine = self.env["stock.last.view.value"]
        self.results = [ReportLine.new(line).id for line in stock_card_results]

    def _compute_results_stock(self):
        self.ensure_one()
        locations = self.env["stock.location"]
        date_from = self.start_date
        date_to = self.end_date
        product_tmpl_ids = self.env['product.template'].search([('product_classification', 'in', ('bahanbaku', 'barangsetengahjadi'))])
        product_ids = self.env['product.product'].search([('product_tmpl_id', 'in', product_tmpl_ids.ids)])
        account_ids = product_ids.mapped('categ_id.property_stock_valuation_account_id').ids
        query2 = """
            SELECT am.date, sm.product_id, sm.product_qty, sm.product_uom_qty, sm.product_uom, 
                CASE WHEN sm.origin_returned_move_id IS NOT NULL then sp.name 
                    WHEN sm.picking_id IS NOT NULL then sp.name
                    WHEN sm.inventory_id IS NOT NULL then si.name
                    WHEN sm.production_id IS NOT NULL then mp.name
                    else TRIM(REPLACE(REPLACE(aml.name, pt.name, ''),'-','')) END as order, 
                pt.name, spt.code, aa.name,
                CASE WHEN sm.origin_returned_move_id IS NOT NULL and spt.code = 'incoming' and sm.purchase_line_id IS NOT NULL then 'Retur to Return Pembelian' 
                    WHEN sm.origin_returned_move_id IS NOT NULL and spt.code = 'outgoing' and sm.purchase_line_id IS NULL then 'Retur to Retur Penjualan'
                    WHEN sm.origin_returned_move_id IS NOT NULL and spt.code = 'incoming' then 'Retur Penjualan' 
                    WHEN sm.origin_returned_move_id IS NOT NULL and spt.code = 'outgoing' then 'Retur Pembelian'
                    WHEN sm.origin_returned_move_id IS NULL and spt.code = 'incoming' then 'Receipt'
                    WHEN sm.origin_returned_move_id IS NULL and spt.code = 'outgoing' then 'Delivery Order'
                    WHEN sm.inventory_id IS NOT NULL then 'Stock Adjustment'
                    WHEN sm.production_id IS NOT NULL then 'Manufacture'
                    WHEN sm.raw_material_production_id IS NOT NULL then 'Manufacture'
                    WHEN aml.name LIKE %s then 'Scrap'
                    WHEN sm.picking_id IS NULL then 'Adjustment from Product'
                    WHEN sm.scrapped IS TRUE then 'Scrap from IT'
                    else '' END as tipe,
                sm.price_unit as price,
                CASE WHEN aml.quantity > 0.0 then aml.quantity else 0.0 END as product_in,
                CASE WHEN aml.quantity > 0.0 then abs(round(aml.debit / aml.quantity, 2)) else 0.0 END as product_price_in,
                CASE WHEN aml.quantity > 0.0 then aml.debit else 0.0 END as product_total_in,
                CASE WHEN aml.quantity < 0.0 then abs(aml.quantity) else 0.0 END as product_out,
                CASE WHEN aml.quantity < 0.0 then abs(round(aml.credit / aml.quantity, 2)) else 0.0 END as product_price_out,
                CASE WHEN aml.quantity < 0.0 then abs(aml.credit) else 0.0 END as product_total_out,
                CASE WHEN sm.date <= %s then True else True end as is_initial,
                aml.balance,
                pt.name as product_name,
                pp.default_code as code_product,
                sm.company_id as company_id
                    from account_move_line aml
                left join account_move am ON aml.move_id = am.id
                left join stock_move sm ON am.stock_move_id = sm.id
                left join stock_picking sp ON sm.picking_id = sp.id
                left join stock_picking_type spt ON sp.picking_type_id = spt.id
                left join product_product pp ON sm.product_id = pp.id
                left join product_template pt ON pp.product_tmpl_id = pt.id
                left join account_account aa ON aml.account_id = aa.id
                left join stock_inventory si ON	sm.inventory_id = si.id
                left join mrp_production mp ON sm.production_id = mp.id
                where 
                    aa.id in %s
                    and pt.product_classification in ('bahanbaku', 'barangsetengahjadi')
                    and CAST(am.date AS date) <= %s
                    and CAST(am.date AS date) >= %s
                order by am.date, am.id
        """
        #new
        self._cr.execute(
            query2,
            ('%Scrap%',
                date_to,
                tuple(account_ids),
                date_to,
                date_from
            ),
        )
        
        stock_card_results = self._cr.dictfetchall()
        ReportLine = self.env["stock.last.view.value"]
        self.result_query2 = [ReportLine.new(line).id for line in stock_card_results]

    @api.onchange('start_date','end_date')
    def onchange_date(self):
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                return {
                    'value':{
                        'end_date':'',
                        'start_date':''
                        },
                    'warning':{
                        'title':'Warning',
                        'message':'End date cannot be less than the start date!'
                    }
                }

    def get_product_classification(self, value):
        if value == 'bahanbaku':
            return 'Bahan Baku'
        if value == 'barangsetengahjadi':
            return 'Barang 1/2 Jadi'
        if value == 'barangjadi':
            return 'Barang Jadi'
        if value == 'sparepart':
            return 'Sparepart'
        if value == 'bahankimia':
            return 'Bahan Kimia'
        if value == 'lainlain':
            return 'Lain-Lain'
        if value == '' or not value:
            return 'No Set Classification'

    def get_stock_akhir_balance(self, product_id):
        new_product_id = self.env['product.product'].browse(product_id)
        # account_ids = new_product_id.mapped('categ_id.property_stock_valuation_account_id').ids
        sql = """
        SELECT am.date, sm.product_id, sm.product_qty, sm.product_uom_qty, sm.product_uom, 
                CASE WHEN sm.origin_returned_move_id IS NOT NULL then sp.name 
                    WHEN sm.picking_id IS NOT NULL then sp.name
                    WHEN sm.inventory_id IS NOT NULL then si.name
                    WHEN sm.production_id IS NOT NULL then mp.name
                    else TRIM(REPLACE(REPLACE(aml.name, pt.name, ''),'-','')) END as order, 
                pt.name, spt.code, aa.name,
                CASE WHEN sm.origin_returned_move_id IS NOT NULL and spt.code = 'incoming' and sm.purchase_line_id IS NOT NULL then 'Retur to Return Pembelian' 
                    WHEN sm.origin_returned_move_id IS NOT NULL and spt.code = 'outgoing' and sm.purchase_line_id IS NULL then 'Retur to Retur Penjualan'
                    WHEN sm.origin_returned_move_id IS NOT NULL and spt.code = 'incoming' then 'Retur Penjualan' 
                    WHEN sm.origin_returned_move_id IS NOT NULL and spt.code = 'outgoing' then 'Retur Pembelian'
                    WHEN sm.origin_returned_move_id IS NULL and spt.code = 'incoming' then 'Receipt'
                    WHEN sm.origin_returned_move_id IS NULL and spt.code = 'outgoing' then 'Delivery Order'
                    WHEN sm.inventory_id IS NOT NULL then 'Stock Adjustment'
                    WHEN sm.production_id IS NOT NULL then 'Manufacture'
                    WHEN sm.raw_material_production_id IS NOT NULL then 'Manufacture'
                    WHEN aml.name LIKE %s then 'Scrap'
                    WHEN sm.picking_id IS NULL then 'Adjustment from Product'
                    WHEN sm.scrapped IS TRUE then 'Scrap from IT'
                    else '' END as tipe,
                sm.price_unit as price,
                CASE WHEN aml.quantity > 0.0 then aml.quantity else 0.0 END as product_in,
                CASE WHEN aml.quantity > 0.0 then abs(round(aml.debit / aml.quantity, 2)) else 0.0 END as product_price_in,
                CASE WHEN aml.quantity > 0.0 then aml.debit else 0.0 END as product_total_in,
                CASE WHEN aml.quantity < 0.0 then abs(aml.quantity) else 0.0 END as product_out,
                CASE WHEN aml.quantity < 0.0 then abs(round(aml.credit / aml.quantity, 2)) else 0.0 END as product_price_out,
                CASE WHEN aml.quantity < 0.0 then abs(aml.credit) else 0.0 END as product_total_out,
                CASE when sm.date <= %s then True else True end as is_initial,
                aml.balance,
                pt.name as product_name,
                pp.default_code as code_product
                    from account_move_line aml
                left join account_move am ON aml.move_id = am.id
                left join stock_move sm ON am.stock_move_id = sm.id
                left join stock_picking sp ON sm.picking_id = sp.id
                left join stock_picking_type spt ON sp.picking_type_id = spt.id
                left join product_product pp ON sm.product_id = pp.id
                left join product_template pt ON pp.product_tmpl_id = pt.id
                left join account_account aa ON aml.account_id = aa.id
                left join stock_inventory si ON	sm.inventory_id = si.id
                left join mrp_production mp ON sm.production_id = mp.id
                where 
                    sm.product_id in %s
                    and CAST(am.date AS date) <= %s
                    and CAST(am.date AS date) >= %s
                order by am.date, am.id
        """
        self._cr.execute(
            sql,
            ('%Scrap%',
                self.end_date,
                tuple([product_id]),
                self.end_date,
                self.start_date,
            ),
        )
        stock_card_results = self._cr.dictfetchall()
        # ReportLine = self.env["stock.last.view"]
        # self.results = [ReportLine.new(line).id for line in stock_card_results]
        return stock_card_results

    def get_opening_quantity(self, product_id):
        #PCI CODE
        qty_start = 0.0
        ##############################################################
        ## beginning balance in
        ##############################################################
        sql = "select sum(product_uom_qty) as qty_open from stock_move as sm " \
                "where sm.product_id= %s " \
                "and sm.location_dest_id in (select id from stock_location where company_id = %s and usage = 'internal' and active = True) " \
                "and sm.state = 'done'" \
                "and sm.date <= '%s'" % (product_id, self.company_id.id, self.start_date)
        self.env.cr.execute(sql)
        result = self.env.cr.dictfetchall()
        for res in result:
            if res.get('qty_open'):
                qty_start = res.get('qty_open')
        ##############################################################
        ## beginning balance out
        ##############################################################
        sql = "select sum(product_uom_qty) as qty_open from stock_move as sm " \
                "where sm.product_id= %s " \
                "and sm.location_id in (select id from stock_location where company_id = %s and usage = 'internal' and active = True) " \
                "and sm.state = 'done'" \
                "and sm.date <= '%s'" % (product_id, self.company_id.id, self.start_date)
        self.env.cr.execute(sql)
        result = self.env.cr.dictfetchall()
        for res in result:
            if res.get('qty_open'):
                qty_start = qty_start - res.get('qty_open')
        return qty_start

    def generate_report_excel(self):
        """function for generate report excel"""
        str_start_date = str(self.start_date)+' 00:00:00'
        str_end_date = str(self.end_date)+' 23:59:59'
        sql1="""
                with
                    product_production as (
                        with product as(
                        select pp.id as product_id, pp.default_code, pt.name
                        from product_template pt
                            left join product_product pp on pp.product_tmpl_id = pt.id
                        where product_classification in ('barangjadi', 'barangsetengahjadi') and pt.active = True),

                        production as (
                        select mp.product_id, sum(mp.product_qty) as qt, sum(mp.bom_amount) as bom_amount, sum(mp.produksi_amount) as produksi_amount,
                            sum(mp.reject_produksi_qty) as reject_qty, sum(mp.reject_produksi_amount) as reject_amount
                        from product_template pt
                            left join product_product pp on pp.product_tmpl_id = pt.id
                            left join mrp_production mp on mp.product_id = pp.id
                        where mp.state in ('done', 'waiting_qc', 'qc_done') and pt.product_classification in ('barangjadi', 'barangsetengahjadi')
                        and mp.date_planned_start >= %s 
                        and mp.date_planned_start <= %s
                        and mp.company_id = %s
                        and pt.active = True
                        group by mp.product_id, pp.default_code, pt.name
                        order by pp.default_code)

                    select * from product full join production on product.product_id = production.product_id
                    )

                    select * from product_production order by default_code"""
        
        params = (str_start_date, str_end_date, self.company_id.id)
        self.env.cr.execute(sql1, params)
        result_sql1 = self.env.cr.fetchall()
        if not result_sql1:
            raise Warning(_("Sorry, There is no data in the selected period."))

        
        sql2 = ''' 
                with
                    product_production as (
                        with product as(
                        select pp.id as product_id, pt.product_classification, pp.default_code, pt.name
                        from product_template pt
                            left join product_product pp on pp.product_tmpl_id = pt.id
                        where product_classification in ('bahanbaku', 'barangsetengahjadi') and pt.active = True),

                        production as (
                        select sm.product_id, sum(sm.product_qty) as qty, sum(sm.bom_amount) as bom_amount, sum(sm.produksi_amount) as produksi_amount,
                            sum(sm.reject_produksi_qty) as reject_qty, sum(sm.reject_produksi_amount) as reject_amount
                        from stock_move sm
                            left join product_product pp on sm.product_id = pp.id
                            left join product_template pt on pp.product_tmpl_id = pt.id
                            left join mrp_production mp on sm.raw_material_production_id = mp.id
                        where mp.state in ('done', 'waiting_qc', 'qc_done') 
                            and pt.product_classification in ('bahanbaku', 'barangsetengahjadi')
                        and mp.date_planned_start >= %s 
                        and mp.date_planned_start <= %s
                        and mp.company_id = %s
                        and pt.active = True
                        group by sm.product_id, pp.default_code
                        order by pp.default_code)


                    select * from product 
                        full join production on product.product_id = production.product_id
                    )

                    select * from product_production order by default_code, product_classification
            '''
        params = (str_start_date, str_end_date, self.company_id.id,)
        self.env.cr.execute(sql2, params)
        result_sql2 = self.env.cr.fetchall()
        if not result_sql2:
            raise Warning(_("Sorry, There is no data in the selected period."))

        fp = io.BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        filename = 'Laporan Mutasi Inventory (Periode %s s/d %s).xlsx'  % (self.start_date, self.end_date)

        #### STYLE
        #################################################################################
        top_style = workbook.add_format({'bold': 1, 'valign':'vcenter'})
        top_style.set_font_name('Calibri')
        top_style.set_font_size('18')
        #################################################################################
        header_style = workbook.add_format({'bold': 1, 'align':'center', 'valign':'vcenter'})
        header_style.set_border()
        header_style.set_font_name('Calibri')
        header_style.set_font_size('13')
        header_style.set_text_wrap()
        header_style.set_bg_color('#eeeeee')
        #################################################################################
        total_style = workbook.add_format({'bold': 1, 'valign':'vcenter', 'align':'right'})
        total_style.set_border()
        total_style.set_font_name('Calibri')
        total_style.set_font_size('12')
        total_style.set_text_wrap()
        total_style.set_bg_color('#eeeeee')
        #################################################################################
        normal_style_left = workbook.add_format({'valign':'vcenter', 'align':'left'})
        normal_style_left.set_border()
        normal_style_left.set_text_wrap()
        normal_style_left.set_font_name('Calibri')
        normal_style_left.set_font_size('12')
        #################################################################################
        normal_center = workbook.add_format({'valign':'vcenter', 'align':'center'})
        normal_center.set_border()
        normal_center.set_text_wrap()
        normal_center.set_font_name('Calibri')
        normal_center.set_font_size('12')
        #################################################################################
        normal_style_right = workbook.add_format({'valign':'vcenter', 'align':'right', 'num_format': '#,##0.00'})
        normal_style_right.set_border()
        normal_style_right.set_text_wrap()
        normal_style_right.set_font_name('Calibri')
        normal_style_right.set_font_size('12')
        #################################################################################
        normal_style_right_bold = workbook.add_format({'valign':'vcenter', 'align':'right', 'num_format': '#,##0.00',
                                                       'bold': 1})
        normal_style_right_bold.set_border()
        normal_style_right_bold.set_text_wrap()
        normal_style_right_bold.set_font_name('Calibri')
        normal_style_right_bold.set_font_size('12')
        #################################################################################
        normal_percent = workbook.add_format({'valign':'vcenter', 'align':'right',
                                              'num_format': '0.00%'})
        normal_percent.set_border()
        normal_percent.set_text_wrap()
        normal_percent.set_font_name('Calibri')
        normal_percent.set_font_size('12')
        #################################################################################
        normal_percent_bold = workbook.add_format({'valign':'vcenter', 'align':'right',
                                              'num_format': '0.00%', 'bold': 1})
        normal_percent_bold.set_border()
        normal_percent_bold.set_text_wrap()
        normal_percent_bold.set_font_name('Calibri')
        normal_percent_bold.set_font_size('12')
        #################################################################################
        
        
        #sheet 1 barang jadi
        worksheet1 = workbook.add_worksheet("Losses Barang Jadi")
        worksheet1.set_column('A:A', 10)
        worksheet1.set_column('B:B', 30)
        worksheet1.set_column('C:C', 10)
        worksheet1.set_column('D:AG', 15)

        worksheet1.set_row(0, 26)
        worksheet1.set_row(1, 26)
        worksheet1.set_row(2, 26)
        worksheet1.write('A1', 'Losses Barang Jadi', top_style)
        worksheet1.write('A2', 'Periode : '+str(self.start_date)+' s/d '+str(self.end_date), top_style)
        worksheet1.write('A3',  self.company_id.name, top_style)

        # ----------
        row = 4
        #header
        #row col row col
        worksheet1.write(row+1, 0, 'Kode', header_style)
        worksheet1.write(row+1, 1, 'Nama Barang', header_style)
        worksheet1.write(row+1, 2, 'Hasil Produksi', header_style)
        worksheet1.write(row+1, 3, 'Adjustment', header_style)
        worksheet1.write(row+1, 4, 'Scrap', header_style)
        worksheet1.write(row+1, 5, 'Total Loss', header_style)
        worksheet1.write(row+1, 6, 'Penjualan', header_style)
        worksheet1.write(row+1, 7, 'Forecast', header_style)

        total_qty = 0.0
        total_qty_do = 0.0
        total_qty_adj = 0.0
        total_qty_scrap = 0.0
        total_qty_loss = 0.0
        total_value_loss = 0.0

        for data in result_sql1:
            forecast_qty_ids = self.env['mrp.rph.line'].search([('product_id','=', data[0]),('company_id','=', self.company_id.id),('date','>=',self.start_date),('date','<=',self.end_date)])
            forecast_qty = sum(forecast_qty_ids.mapped('qty_forecast'))
            
            initial = self._get_initial(self.results.filtered(lambda l: l.product_id.id == data[0] and l.is_initial and l.tipe == 'Manufacture'))
            initial_do = abs(self._get_initial(self.results.filtered(lambda l: l.product_id.id == data[0] and l.is_initial and l.tipe in ('Delivery Order','Retur Penjualan','Retur to Retur Penjualan'))))        
            initial_scrap = self._get_initial(self.results.filtered(lambda l: l.product_id.id == data[0] and 'scrap' in l.tipe.lower().split(' ')))
            
            initial_adjust = self._get_initial(self.results.filtered(lambda l: l.product_id.id == data[0] and 'adjustment' in l.tipe.lower().split(' ')))
            
            initial_adj_scrap = initial_adjust + initial_scrap
        
            worksheet1.write(row+2, 0, data[1], normal_style_left)
            worksheet1.write(row+2, 1, data[2], normal_style_left)
            #saldo inventory
            worksheet1.write(row+2, 2, initial, normal_style_right)
                   
            #adj
            worksheet1.write(row+2, 3, initial_adjust, normal_style_right)
             
            #scrap
            worksheet1.write(row+2, 4, initial_scrap, normal_style_right)
            
            #total loss
            worksheet1.write(row+2, 5, initial_adjust + initial_scrap, normal_style_right)
            
            worksheet1.write(row+2, 6, initial_do, normal_style_right)
            worksheet1.write(row+2, 7, forecast_qty, normal_style_right)

            total_qty += initial

            total_qty_do += initial_do

            total_qty_adj += initial_adjust

            total_qty_scrap += initial_scrap

            total_qty_loss += initial_adj_scrap

            row += 1
        worksheet1.write(row+2, 2, total_qty, normal_style_right_bold)
        worksheet1.write(row+2, 3, total_qty_adj, normal_style_right_bold)
        # worksheet1.write(row+2, 6, total_value_adj, normal_style_right_bold)
        worksheet1.write(row+2, 4, total_qty_scrap, normal_style_right_bold)
        # worksheet1.write(row+2, 9, total_value_scrap, normal_style_right_bold)
        worksheet1.write(row+2, 5, total_qty_loss, normal_style_right_bold)
        # worksheet1.write(row+2, 12, total_value_loss, normal_style_right_bold)
        # worksheet1.write(row+2, 13, total_value_loss/total_value if total_value > 0.0 else 0.0, normal_percent_bold)
        worksheet1.write(row+2, 6, total_qty_do, normal_style_right_bold)
        worksheet1.write(row+2, 7, forecast_qty, normal_style_right_bold)

        row = 0
        worksheet2 = workbook.add_worksheet("Material Variance Report")
        worksheet2.set_column('A:A', 10)
        worksheet2.set_column('B:B', 30)
        worksheet2.set_column('C:C', 10)
        worksheet2.set_column('D:AG', 15)

        worksheet2.set_row(0, 26)
        worksheet2.set_row(1, 26)
        worksheet2.set_row(2, 26)
        worksheet2.write('A1', 'Material Variance Report', top_style)
        worksheet2.write('A2', 'Periode : '+str(self.start_date)+' s/d '+str(self.end_date), top_style)
        worksheet2.write('A3',  self.company_id.name, top_style)

        # ----------
        row = 4
        #header
        #row col row col
        worksheet2.write(row+1, 0, 'Kode', header_style)
        worksheet2.write(row+1, 1, 'Nama Barang', header_style)
        worksheet2.write(row+1, 2, 'Pemakaian Sesuai Standard', header_style)
        worksheet2.write(row+1, 3, 'Realisasi Pemakaian', header_style)
        worksheet2.write(row+1, 4, 'Adjustment', header_style)
        worksheet2.write(row+1, 5, 'Scrap', header_style)
        worksheet2.write(row+1, 6, 'Scrap', header_style)
        worksheet2.write(row+1, 7, 'Losses (%)', header_style)
        classification = ''
        #selisih = standar - realisasi - scrap -adj
        for data in result_sql2:
            avg = 0
            qty_bom = 0
            
            data_5 = data[5] if data[5] else 0.0
            data_6 = data[6] if data[6] else 0.0
            data_7 = data[7] if data[7] else 0.0
            data_8 = data[8] if data[8] else 0.0
            
            initial_scrap = self._get_initial(self.result_query2.filtered(lambda l: l.product_id.id == data[0] and l.company_id.id == self.company_id.id and 'scrap' in l.tipe.lower().split(' ')))
            nilai_akhir_scrap = self._get_initial_balance(self.result_query2.filtered(lambda l: l.product_id.id == data[0] and 'scrap' in l.tipe.lower().split(' ')))
            # avg_scrap = nilai_akhir_scrap / initial_scrap if initial_scrap > 0.0  else 0.0
            initial_adjust = self._get_initial(self.result_query2.filtered(lambda l: l.product_id.id == data[0] and l.company_id.id == self.company_id.id and 'adjustment' in l.tipe.lower().split(' ')))
            nilai_akhir_adjust = self._get_initial_balance(self.result_query2.filtered(lambda l: l.product_id.id == data[0] and 'adjustment' in l.tipe.lower().split(' ')))
            # avg_adj = nilai_akhir_adjust / initial_adjust if initial_adjust > 0.0 else 0.0

            if data[1] and data[1] != classification:
                text = ''
                if data[1] == 'bahanbaku':
                    text = 'Bahan Baku'
                if data[1] == 'barangsetengahjadi':
                    text = 'Barang Setengah Jadi'
                worksheet2.merge_range(row+2, 0, row+2, 7, text, header_style)
                row += 1
            
            qty_bom = data_5 - data_8
            if qty_bom != 0:
                avg = data_6/qty_bom
            worksheet2.write(row+2, 0, data[2], normal_style_left)
            worksheet2.write(row+2, 1, data[3], normal_style_left)
            #sesuai standard
            worksheet2.write(row+2, 2, qty_bom, normal_style_right)
            
            #realisasi
            realisasi_qty = data_5
            worksheet2.write(row+2, 3, realisasi_qty, normal_style_right)            
            #adj
            worksheet2.write(row+2, 4, initial_adjust, normal_style_right)            
            #scrap
            worksheet2.write(row+2, 5, initial_scrap, normal_style_right)            
            #selisih pemakaian
            worksheet2.write(row+2, 6, qty_bom - realisasi_qty - initial_adjust - initial_scrap, normal_style_right)
            loss = 0.0
            if data_5 != 0 and data_6 != 0:
                loss = (round(avg, 2) * (qty_bom - realisasi_qty)) / data_6
            worksheet2.write(row+2, 7, loss, normal_percent)
            
            row += 1
            classification = data[1]


        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'state':'get', 'data':out, 'name': filename})
        ir_model_data = self.env['ir.model.data']
        fp.close()

        form_res = ir_model_data.get_object_reference('sanqua_mutasi_inventory_report','mutasi_inventory_wizard_form_view_without_value')
        form_id = form_res and form_res[1] or False
        return {
            'name'  : 'Download XLS',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.mutasi.inventory.report.value',
            'res_id': self.id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }

    def _get_initial(self, product_line):
        product_input_qty = sum(product_line.mapped("product_in"))
        product_output_qty = sum(product_line.mapped("product_out"))
        print ('_get_initial', product_input_qty, product_output_qty)
        return product_input_qty - product_output_qty

    def _get_initial_balance(self, product_line):
        product_input_balance = sum(product_line.mapped("product_total_in"))
        product_output_balance = sum(product_line.mapped("product_total_out"))
        return product_input_balance - product_output_balance