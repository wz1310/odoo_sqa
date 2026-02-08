
from odoo import api, fields, models
import math

class StockCardReport( models.TransientModel ):
    _inherit = "report.stock.card.report"

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

        query2 = """
            SELECT ( am.date + interval '7' HOUR) as "date", sm.product_id, sm.product_qty, sm.product_uom_qty, sm.product_uom, 
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
                CASE when ( sm.date + interval '7' HOUR) < %s then True else False end as is_initial,
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
                    and CAST(( am.date + interval '7' HOUR) AS date) <= %s
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

        # print(">>> INHERITED....")

        print(">>> date_from : " + str(date_from))
        print(">>> date_to : " + str(self.date_to))
        print(">>> account_ids : " + str(tuple(account_ids)))
        print(">>> product_ids : " + str(tuple(self.product_ids.ids)))

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

    def print_report(self, report_type="qweb"):
        self.ensure_one()
        action = (
            report_type == "xlsx"
            and self.env.ref("stock_card_report.action_stock_card_report_xlsx")
            or self.env.ref("stock_card_report.action_stock_card_report_pdf")
        )
        return action.report_action(self, config=False)