from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class SaleOrderTruck(models.Model):
    _inherit = "sale.order.truck"

    def reg_card_as_borrow(self, pickings):
        self = self.sudo()
        self.ensure_one()
        pickings = pickings.sudo()
        pickings = pickings.filtered(lambda r:r.partner_id.id != False and len(r.partner_id.ref_company_ids)==0)
        for picking in pickings:
            for rec in picking.move_lines.filtered(lambda r: r.product_id.reg_in_customer_stock_card == True):
                material = self.sale_truck_material_ids.filtered(
                    lambda r:r.partner_id.id == picking.sale_id.partner_id.id 
                    and r.product_id.id==rec.product_id.id and r.non_sanqua==False)
                if not len(material):
                    raise UserError(_("No Sale Truck Lines matched with criteria when reg_card_as_borrow.\nCriteria: %s") % ("partner="+picking.sudo().sale_id.sudo().partner_id.display_name,))
                
                vals = {
                    'sale_truck_id':self.id,
                    'order_type': 'borrow',
                    'picking_id' :picking.id,
                    'origin' :picking.name,
                    'partner_id' : picking.partner_id.id,
                    'company_id' : picking.company_id.id,
                    'transaction_date' : picking.date_done,
                    'product_id' : rec.product_id.id,
                    'qty' : material.delivered_qty
                }

                sale_truck_status_id = self.env['sale.truck.item.status'].create(vals)

    def reg_card_as_returned(self, picking=None):
        self.ensure_one()
        self = self.sudo()
        if not picking:
            picking = self.sudo().return_material_picking

        return_material_ids = self.sale_truck_material_ids.filtered(lambda r:r.return_qty>0.0)

        for material in return_material_ids:
            vals = {
                'sale_truck_id':self.id,
                'order_type': 'returned',
                'picking_id' : picking.sudo().id,
                'origin' : "SOT Return "+picking.sudo().name,
                'partner_id' : material.partner_id.id,
                'company_id' : material.sale_truck_id.company_id.id,
                'transaction_date' : picking.sudo().date_done,
                'product_id' : material.product_id.id,
                'qty' : material.return_qty
            }
            sale_truck_status_id = self.env['sale.truck.item.status'].create(vals)


    def btn_post(self):
        res = super(SaleOrderTruck, self).btn_post()
        picking_ids = self.env['stock.picking'].browse(res)
        for picking in picking_ids:
            self.sudo().reg_card_as_borrow(picking)
        self.sudo().reg_card_as_returned()
        return res