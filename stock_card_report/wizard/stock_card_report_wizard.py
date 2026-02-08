# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
import math

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval
from io import BytesIO

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

class StockCardReportWizard(models.TransientModel):
    _name = "stock.card.report.wizard"
    _description = "Stock Card Report Wizard"

    stock_file_data = fields.Binary('Stock Movement File')
    date_range_id = fields.Many2one(comodel_name="date.range", string="Period")
    date_from = fields.Date(string="Start Date",default=fields.Date.context_today)
    date_to = fields.Date(string="End Date",default=fields.Date.context_today)
    location_id = fields.Many2one(
        comodel_name="stock.location", string="Location"
    )
    product_ids = fields.Many2many(
        comodel_name="product.product", string="Products", required=True
    )
    price = fields.Boolean("Show Price",default=False)

    results = fields.Many2many(
        comodel_name="stock.card.view",
        help="Use compute fields, so there is nothing store in database",
    )
    name = fields.Char(string="Filename", readonly=True)
    data_file = fields.Binary(string="File", readonly=True)

    @api.onchange("date_range_id")
    def _onchange_date_range_id(self):
        self.date_from = self.date_range_id.date_start
        self.date_to = self.date_range_id.date_end

    def button_export_html(self):
        self.ensure_one()
        action = self.env.ref("stock_card_report.action_report_stock_card_report_html")
        vals = action.read()[0]
        context = vals.get("context", {})
        if context:
            context = safe_eval(context)
        model = self.env["report.stock.card.report"]
        report = model.create(self._prepare_stock_card_report())
        context["active_id"] = report.id
        context["active_ids"] = report.ids
        vals["context"] = context
        return vals

    def button_export_pdf(self):
        self.ensure_one()
        report_type = "qweb-pdf"
        return self._export(report_type)

    def button_export_xlsx(self):
        self.ensure_one()
        return self.generate_excel_report()

    def _prepare_stock_card_report(self):
        self.ensure_one()
        return {
            "date_from": self.date_from,
            "date_to": self.date_to or fields.Date.context_today(self),
            "product_ids": [(6, 0, self.product_ids.ids)],
            "location_id": self.location_id.id,
            "price": self.price,
        }

    def _export(self, report_type):
        model = self.env["report.stock.card.report"]
        report = model.create(self._prepare_stock_card_report())
        return report.print_report(report_type)

    def generate_excel_report(self):
        locations = self.env["stock.location"]
        date_from = self.date_from or "0001-01-01"
        self.date_to = self.date_to or fields.Date.context_today(self)
        if self.location_id:
            locations = self.env["stock.location"].search(
                [("id", "child_of", [self.location_id.id])]
            )
        account_ids = self.product_ids.mapped('categ_id.property_stock_valuation_account_id').ids
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
                CASE when sm.date < %s then True else False end as is_initial,
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
                    aa.id in %s
                    and sm.product_id in %s
                    and CAST(am.date AS date) <= %s
                order by am.date, am.id
        """
        #new
        self._cr.execute(
            query2,
            ('%Scrap%',
                date_from,
                tuple(account_ids),
                tuple(self.product_ids.ids),
                self.date_to,
            ),
        )
        stock_card_results = self._cr.dictfetchall()
        ReportLine = self.env["stock.card.view"]
        
        self.results = [ReportLine.create(line).id for line in stock_card_results]
        
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

        worksheet.set_column('A:B', 20)
        worksheet.set_column('C:E', 30)
        worksheet.set_column('F:Z', 20)

        date_from = str(self.date_from) or " "
        date_to = str(self.date_to) or str(fields.Date.context_today(self))
        location_id = self.location_id.name or " "
        name_product = ''
        
        row = 0
        for prod in self.product_ids:
            name_product = prod.name
            kode_product = prod.default_code
            # ========== HEADER ==============
            worksheet.merge_range(row, 0, row, 13, 'Stock Card - '+ name_product, header_table_left)
            worksheet.write(row+2, 0, 'Date From', header_table)
            worksheet.write(row+2, 1, 'Date To', header_table)
            worksheet.write(row+2, 2, 'Location', header_table)
            worksheet.write(row+3, 0, date_from if self.date_from else " ", header_table)
            worksheet.write(row+3, 1, date_to, header_table)
            worksheet.write(row+3, 2, location_id, header_table)

            worksheet.write(row+5, 0, 'Date', header_table)
            worksheet.write(row+5, 1, 'Code', header_table)
            worksheet.write(row+5, 2, 'Product', header_table)
            worksheet.write(row+5, 3, 'Reference', header_table)
            worksheet.write(row+5, 4, 'No.Order', header_table)
            worksheet.write(row+5, 5, 'In Qty', header_table)
            worksheet.write(row+5, 6, 'In Cost', header_table)
            worksheet.write(row+5, 7, 'Nilai Masuk', header_table)
            worksheet.write(row+5, 8, 'Out Qty', header_table)
            worksheet.write(row+5, 9, 'Out Cost', header_table)
            worksheet.write(row+5, 10, 'Nilai Keluar', header_table)
            worksheet.write(row+5, 11, 'Qty Akhir', header_table)
            worksheet.write(row+5, 12, 'Biaya / Unit', header_table)
            worksheet.write(row+5, 13, 'Nilai Akhir', header_table)
            #header
            
            initial = self._get_initial(self.results.filtered(lambda l: l.product_id == prod and l.is_initial))
            nilai_akhir = self._get_initial_balance(self.results.filtered(lambda l: l.product_id == prod and l.is_initial))
            biaya_per_unit_akhir = 0.0
            if nilai_akhir > 0:
                biaya_per_unit_akhir = self.truncate(nilai_akhir / initial, 2)
            
            worksheet.write(row+6, 0, '', body_table_left)
            worksheet.write(row+6, 1, kode_product, body_table_center)
            worksheet.write(row+6, 2, name_product, body_table_left)
            worksheet.write(row+6, 3, 'Stock Awal', body_table_center)
            worksheet.write(row+6, 4, '', body_table_left)
            worksheet.write(row+6, 5, '', body_table_des)
            worksheet.write(row+6, 6, '', body_table_des)
            worksheet.write(row+6, 7, '', body_table_des)
            worksheet.write(row+6, 8, '', body_table_des)
            worksheet.write(row+6, 9, '', body_table_des)
            worksheet.write(row+6, 10, '', body_table_des)
            worksheet.write(row+6, 11, initial, body_table_des)
            worksheet.write(row+6, 12, biaya_per_unit_akhir, body_table_des)
            worksheet.write(row+6, 13, nilai_akhir, body_table_des)

            row += 1
            for res in self.results.filtered(lambda l: l.product_id == prod and not l.is_initial):
                initial = initial + res.product_in - res.product_out
                nilai_akhir = nilai_akhir + res.product_total_in - res.product_total_out
                biaya_per_unit_akhir = 0.0
                if nilai_akhir > 0:
                    biaya_per_unit_akhir = self.truncate(nilai_akhir / initial, 2)
                worksheet.write(row+6, 0, str(res.date.date() if res.date else ''), body_table_center)
                worksheet.write(row+6, 1, res.code_product, body_table_center)
                worksheet.write(row+6, 2, res.product_name, body_table_left)
                worksheet.write(row+6, 3, res.tipe, body_table_left)
                worksheet.write(row+6, 4, res.order, body_table_left)
                worksheet.write(row+6, 5, res.product_in, body_table_des)
                worksheet.write(row+6, 6, res.product_price_in, body_table_des)
                worksheet.write(row+6, 7, res.product_total_in, body_table_des)
                worksheet.write(row+6, 8, res.product_out, body_table_des)
                worksheet.write(row+6, 9, res.product_price_out, body_table_des)
                worksheet.write(row+6, 10, res.product_total_out, body_table_des)
                worksheet.write(row+6, 11, initial, body_table_des)
                worksheet.write(row+6, 12, biaya_per_unit_akhir, body_table_des)
                worksheet.write(row+6, 13, nilai_akhir, body_table_des)
                row += 1
            row += 10

        workbook.close()
        out = base64.b64encode(fp.getvalue())
        fp.close()
        file_name = "inventory_stock_report.xlsx"
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

    def _get_initial(self, product_line):
        product_input_qty = sum(product_line.mapped("product_in"))
        product_output_qty = sum(product_line.mapped("product_out"))
        return product_input_qty - product_output_qty

    def _get_initial_balance(self, product_line):
        product_input_balance = sum(product_line.mapped("product_total_in"))
        product_output_balance = sum(product_line.mapped("product_total_out"))
        return product_input_balance - product_output_balance

    def truncate(self,number, decimals=0):
        """
        Returns a value truncated to a specific number of decimal places.
        """
        if not isinstance(decimals, int):
            raise TypeError("decimal places must be an integer.")
        elif decimals < 0:
            raise ValueError("decimal places has to be 0 or more.")
        elif decimals == 0:
            return math.trunc(number)

        factor = 10.0 ** decimals
        return math.trunc(number * factor) / factor