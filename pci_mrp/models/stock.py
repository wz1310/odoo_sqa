from odoo import fields,api,models,_
from odoo.exceptions import UserError
from datetime import datetime

class stockmove(models.Model):
    _inherit = 'stock.move'
    

    reject_produksi_qty = fields.Float('Reject Production (Qty)', store=True)
    reject_produksi_persen = fields.Float('Reject Production (%)', store=True)
    reject_produksi_amount = fields.Float('Reject Amount (Rp)', store=True)
    bom_amount = fields.Float('BoM Amount (Rp)', store=True)
    produksi_amount = fields.Float('FG Amount (Rp)', store=True)
    

    # @api.depends('state')
    # def _compute_reject_produksi_qty(self):     
    #     for row in self:
    #         if row:
    #             if row.raw_material_production_id and not row.state == 'done' and row.product_uom_qty > 0 and row.quantity_done > 0 and not row.reference == 'New':
    #                 row.reject_produksi_qty = row.quantity_done - row.product_uom_qty
    #                 row.reject_produksi_persen = (row.reject_produksi_qty / row.product_uom_qty) * 100
    #                 row.reject_produksi_amount = row.reject_produksi_qty * row.product_id.standard_price
    #                 row.bom_amount = row.product_uom_qty * row.product_id.standard_price
    #                 row.produksi_amount = row.quantity_done * row.product_id.standard_price
                    
        
    # def _update_init(self):
    #     for row in self.search([]):
    #         row.reject_produksi_qty = 0.0
    #         row.reject_produksi_persen = 0.0
    #         row.reject_produksi_amount = 0.0
    #         if row.raw_material_production_id and not row.state == 'done' and row.product_uom_qty > 0 and row.quantity_done > 0:
    #             row.reject_produksi_qty = row.quantity_done - row.product_uom_qty
    #             row.reject_produksi_persen = (row.reject_produksi_qty / row.product_uom_qty) * 100
    #             row.reject_produksi_amount = row.reject_produksi_qty * row.product_id.standard_price
    #             row.bom_amount = row.product_uom_qty * row.product_id.standard_price
    #             row.produksi_amount = row.quantity_done * row.product_id.standard_price

        