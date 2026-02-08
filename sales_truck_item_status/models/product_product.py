"""File sale order truck"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class ProdutProduct(models.Model):
    _inherit = "product.product"

    sale_truck_dispenser = fields.Boolean(related='product_tmpl_id.sale_truck_dispenser', string='Dispenser', track_visibility='onchange')
    # qty_field = fields.Selection([
    #     ('delivered_qty', 'Delivered'),
    #     ('difference_qty', 'Different')
    # ], string='Qty Computation Source',related='product_tmpl_id.qty_field')

    # @api.constrains('reg_in_customer_stock_card')
    # def _constrains_reg_in_customer_stock_card(self):
    #     for rec in self:
    #         if rec.reg_in_customer_stock_card == False:
    #             rec.qty_field = 'delivered_qty'