from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class SaleTruckItemStatusPartnerReport(models.Model):
    _name = "sale.truck.item.status.partner.report"
    _description = "Partner Stock Card (Galon)"
    _order = "delivery_date"


    partner_id = fields.Many2one('res.partner', string="Customer", readonly=True)
    product_id = fields.Many2one('product.product', string="Product", readonly=True)
    # total = fields.Float("Total", readonly=True)
    # total_exclude_deposit = fields.Float("Total Excl. Deposit", readonly=True)
    delivery_date = fields.Date(string='Date')
    sale_truck_id = fields.Many2one('sale.order.truck', string='Sale Truck')
    picking_id = fields.Many2one('stock.picking', string='Delivery Order')
    borrow_qty = fields.Float(string='Borrow')
    returned_qty = fields.Float(string='Returned')
    changed_qty = fields.Float(string='Changed')
    replaced_qty = fields.Float(string='To Bill')
    deposito_qty = fields.Float(string='Deposito')
    
    

    _auto = False
    def _select(self):
        query = """
            SELECT 
            id,
            delivery_date,
            partner_id,
            product_id,
            NULL::INT as sale_truck_id,
            NULL::INT as picking_id,
            borrow_qty,
            0.0 as returned_qty, 
            deposito_qty * -1 as changed_qty, 
            0.0 as replaced_qty,
            0.0 as deposito_qty
            FROM adjustment_galon
            UNION
            SELECT 
            id,
            date_deposito as delivery_date,
            partner_id,
            NULL::INT as product_id,
            NULL::INT as sale_truck_id,
            NULL::INT as picking_id,
            0.0 as borrow_qty,
            0.0 as returned_qty, 
            0.0 as changed_qty, 
            0.0 as replaced_qty,
            qty as deposito_qty
            FROM sales_truck_item_adjustment
            UNION

            SELECT 
            CONCAT(lpad(sot_material.partner_id::TEXT, 5,'0'),rpad(sm.product_id::TEXT,4,'0'),rpad(sot.id::TEXT,3,'0'),rpad(sp.id::TEXT,4,'0'))::BIGINT as id,
            sp.date_done::Date as delivery_date ,
            sot_material.partner_id,
            sm.product_id,
            sot.id as sale_truck_id,
            sp.id as picking_id,
            sum(sot_material.delivered_qty) - COALESCE(adjustment_returned.qty,0) as borrow_qty,
            sum(sot_material.return_qty + COALESCE(adjustment_returned.qty,0)) * -1 as returned_qty, 
            adjustment_change.qty * -1 as changed_qty, 
            adjustment_bill.qty as replaced_qty,
            0.0 as deposito_qty
        """
        return query
    
    def _from(self):
        query = """
                sale_order_truck sot
            JOIN sale_order_truck_material sot_material ON sot_material.sale_truck_id = sot.id
            JOIN stock_picking sp ON sot.id = sp.sale_truck_id AND sot_material.partner_id = sp.partner_id
            JOIN stock_picking_type spt ON spt.id = sp.picking_type_id
            JOIN stock_move sm ON sp.id = sm.picking_id AND sot_material.product_id = sm.product_id
            JOIN product_product pp ON pp.id = sot_material.product_id
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            LEFT JOIN (SELECT sts.sale_truck_id,sts.partner_id, adj.adjustment_type, sts.product_id, sum(adj.qty) as qty
                    FROM sales_truck_item_adjustment adj
                    JOIN sale_truck_item_status sts ON adj.sale_truck_status_id = sts.id
                    WHERE adj.adjustment_type = 'returned' AND adj.state = 'done'
                    GROUP BY sts.sale_truck_id,sts.partner_id, adj.adjustment_type, sts.product_id) as adjustment_returned ON adjustment_returned.sale_truck_id = sot.id AND adjustment_returned.partner_id = sot_material.partner_id AND adjustment_returned.product_id = sot_material.product_id 
            LEFT JOIN (SELECT sts.sale_truck_id,sts.partner_id, adj.adjustment_type, sts.product_id, sum(adj.qty) as qty
                    FROM sales_truck_item_adjustment adj
                    JOIN sale_truck_item_status sts ON adj.sale_truck_status_id = sts.id
                    WHERE adj.adjustment_type ='change' AND adj.state = 'done'
                    GROUP BY sts.sale_truck_id,sts.partner_id, adj.adjustment_type, sts.product_id) as adjustment_change ON adjustment_change.sale_truck_id = sot.id AND adjustment_change.partner_id = sot_material.partner_id AND adjustment_change.product_id = sot_material.product_id 
            LEFT JOIN (SELECT sts.sale_truck_id,sts.partner_id, adj.adjustment_type, sts.product_id, sum(adj.qty) as qty
                    FROM sales_truck_item_adjustment adj
                    JOIN sale_truck_item_status sts ON adj.sale_truck_status_id = sts.id
                    WHERE adj.adjustment_type ='to_bill' AND adj.state = 'done'
                    GROUP BY sts.sale_truck_id,sts.partner_id, adj.adjustment_type, sts.product_id) as adjustment_bill ON adjustment_bill.sale_truck_id = sot.id AND adjustment_bill.partner_id = sot_material.partner_id AND adjustment_bill.product_id = sot_material.product_id 
            WHERE pt.sale_truck = True AND spt.code = 'outgoing' AND sot.state = 'done'
            GROUP BY sp.date_done::Date,sot_material.partner_id,sm.product_id,sot.id,sp.id,adjustment_change.qty,adjustment_bill.qty,adjustment_returned.qty
        """
        return query
    
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            SELECT galon.id,
            galon.delivery_date,
            galon.partner_id,
            galon.product_id,
            galon.sale_truck_id,
            galon.picking_id,
            galon.borrow_qty,
            galon.returned_qty, 
            galon.changed_qty, 
            galon.replaced_qty,
            galon.deposito_qty FROM (%s
            FROM %s
            ) as galon ORDER BY galon.delivery_date)""" % (self._table, self._select(), self._from()))