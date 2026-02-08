# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
import math

class StockCardView(models.TransientModel):
    _name = "stock.card.view"
    _description = "Stock Card View"
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

class StockCardReport(models.TransientModel):
    _name = "report.stock.card.report"
    _description = "Stock Card Report"

    # Filters fields, used for data computation
    date_from = fields.Date()
    date_to = fields.Date()
    product_ids = fields.Many2many(comodel_name="product.product")
    location_id = fields.Many2one(comodel_name="stock.location")
    price = fields.Boolean()

    # Data fields, used to browse report data
    results = fields.Many2many(
        comodel_name="stock.card.view",
        compute="_compute_results",
        help="Use compute fields, so there is nothing store in database",
    )

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

    def _compute_results(self):
        self.ensure_one()
        locations = self.env["stock.location"]
        date_from = self.date_from or "0001-01-01"
        self.date_to = self.date_to or fields.Date.context_today(self)
        if self.location_id:
            locations = self.env["stock.location"].search(
                [("id", "child_of", [self.location_id.id])]
            )
        account_ids = self.product_ids.mapped('categ_id.property_stock_valuation_account_id').ids
        query1 = """
            SELECT move.date, move.product_id, move.product_qty,
                move.product_uom_qty, move.product_uom, 
                CASE WHEN so.name IS NOT NULL THEN so.name
                WHEN po.name IS NOT NULL THEN po.name
                WHEN move.reference = 'New' THEN pg.name 
                ELSE move.reference END as order,
                CASE WHEN so.name IS NOT NULL THEN CONCAT('Delivery to ', res.name)
                WHEN po.name IS NOT NULL THEN CONCAT('Receipt from ', respik.name)
                WHEN mrp.name IS NOT NULL THEN  CONCAT('MO : ', mrp.name)
                ELSE 'Internal Transfer' END as description,
                move.price_unit as price,
                case when move.location_dest_id in %s
                    then move.price_unit end as price_in,
                case when move.location_id in %s
                    then move.price_unit end as price_out,
                CASE WHEN move.reference = 'New' THEN pg.name ELSE move.reference END as reference,
                move.location_id, move.location_dest_id,
                case when move.location_dest_id in %s
                    then move.product_qty end as product_in,
                case when move.location_id in %s
                    then move.product_qty end as product_out,
                case when move.date < %s then True else False end as is_initial
                
            FROM stock_move move
            LEFT JOIN sale_order_line sol ON sol.id = move.sale_line_id
            LEFT JOIN sale_order so ON so.id = sol.order_id
            LEFT JOIN purchase_order_line pol ON pol.id = move.purchase_line_id
            LEFT JOIN purchase_order po ON po.id = pol.order_id
            LEFT JOIN res_partner res ON res.id = move.partner_id
            LEFT JOIN res_partner respik ON respik.id = move.vendor_id
            LEFT JOIN mrp_production mrp ON mrp.id = move.qc_production_id
            LEFT JOIN procurement_group pg ON pg.id = move.group_id
            WHERE (move.location_id in %s or move.location_dest_id in %s)
                and move.state = 'done' and move.product_id in %s
                and CAST(move.date AS date) <= %s
            ORDER BY move.date, move.id
        """
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
                    else 'Lain-Lain' END as tipe,
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
        
        #old
        # self._cr.execute(
        #     query1,
        #     (
        #         tuple(locations.ids),
        #         tuple(locations.ids),
        #         tuple(locations.ids),
        #         tuple(locations.ids),
        #         date_from,
        #         tuple(locations.ids),
        #         tuple(locations.ids),
        #         tuple(self.product_ids.ids),
        #         self.date_to,
        #     ),
        # )
        
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
        self.results = [ReportLine.new(line).id for line in stock_card_results]

    def _get_initial(self, product_line):
        product_input_qty = sum(product_line.mapped("product_in"))
        product_output_qty = sum(product_line.mapped("product_out"))
        return product_input_qty - product_output_qty

    def _get_initial_balance(self, product_line):
        product_input_balance = sum(product_line.mapped("product_total_in"))
        product_output_balance = sum(product_line.mapped("product_total_out"))
        return product_input_balance - product_output_balance

    def print_report(self, report_type="qweb"):
        self.ensure_one()
        action = (
            report_type == "xlsx"
            and self.env.ref("stock_card_report.action_stock_card_report_xlsx")
            or self.env.ref("stock_card_report.action_stock_card_report_pdf")
        )
        return action.report_action(self, config=False)

    def _get_html(self):
        result = {}
        rcontext = {}
        report = self.browse(self._context.get("active_id"))
        if report:
            rcontext["o"] = report
            result["html"] = self.env.ref(
                "stock_card_report.report_stock_card_report_html"
            ).render(rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self.with_context(given_context)._get_html()
