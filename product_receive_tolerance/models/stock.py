from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockMove(models.Model):
    _inherit = 'stock.move'

    
    def write(self,values):
        
        res = super(StockMove, self).write(values)
        self._constrains_quantity_done()
        return res

    def _constrains_quantity_done(self):
        
        for each in self.filtered(lambda r: r.picking_code=='incoming'):
            qty_tolerance = 0.0
            tolerance = 0.0
            if each.quantity_done:
                qty_order = each.purchase_line_id.product_qty
                if qty_order:
                    qty_received = each.purchase_line_id.qty_received - each.quantity_done
                    if each.product_id.qty_tolerance > 0.0:
                        tolerance = round(qty_order * (each.product_id.qty_tolerance/100), 2)
                    qty_tolerance = round((qty_order + tolerance), 2)
                    
                    qty_remaining = round(qty_tolerance - qty_received, 2)
                    qty_done = round(each.quantity_done, 2)
                    # if qty_done > qty_remaining:
                    #     raise UserError (_("Quantity Tolerance for %s is not met in move!\nQty Done : %s\nQty Remaining : %s") % (each.product_id.name,qty_done,qty_remaining))
                    # elif each.quantity_done > qty_tolerance and each.product_id.qty_tolerance > 0.0: #20 > 22
                    #     raise UserError (_("Quantity Tolerance for %s is not met in move!\nQty Done : %s\nQty Tolerace : %s") % (each.product_id.name,qty_tolerance,each.quantity_done))



class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        if self.picking_type_code == 'incoming':
            self._constrains_quantity_done()
        res = super(StockPicking, self).button_validate()
        return res


    def _constrains_quantity_done(self):
        # qty_demand = 0.0
        # qty_done = 0.0
        # total_tolerance = 0.0
        # last_product = []
        
        for line in self:
            for each in line.move_ids_without_package:
                qty_tolerance = 0.0
                tolerance = 0.0
                qty_order = each.purchase_line_id.product_qty
                if qty_order:
                    qty_received = each.purchase_line_id.qty_received
                    if each.product_id.qty_tolerance > 0.0:
                        tolerance = round(qty_order * (each.product_id.qty_tolerance/100), 2)
                    qty_tolerance = round((qty_order + tolerance), 2)

                    qty_remaining = round(qty_tolerance - qty_received, 2)
                    qty_done = round(each.quantity_done, 2)
                    if qty_done > qty_remaining and each.product_id.qty_tolerance > 0.0:
                        raise UserError (_("Quantity Tolerance for %s is not met in Picking!\nQty Done : %s\nQty Remaining : %s") % (each.product_id.name,qty_done,qty_remaining))



                # if ea.product_id.id not in last_product or not last_product:
                #     last_product.append(ea.product_id.id)
                # for x in self.move_ids_without_package:
                #     if ea.product_id.id == x.product_id.id and ea.product_id.id in last_product:
                #         qty_demand += x.product_uom_qty
                #         qty_done += x.quantity_done
                # total_tolerance = qty_demand * (ea.product_id.qty_tolerance/100)
                # total_tolerance = round(total_tolerance + qty_demand, 2)
                # if qty_done > qty_demand and ea.product_id.qty_tolerance == 0.0:
                #     raise UserError (_("Quantity Tolerance for %s is not met in picking!") % ea.product_id.name)
                # elif qty_done > total_tolerance and ea.product_id.qty_tolerance > 0.0:
                #     raise UserError (_("Quantity Tolerance for %s is not met in picking!") % ea.product_id.name)
                # total_tolerance = 0
                # qty_demand = 0
                # qty_done = 0
                

