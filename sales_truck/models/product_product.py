"""File sale order truck"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class ProdutProduct(models.Model):
    _inherit = "product.product"

    sale_truck = fields.Boolean(related='product_tmpl_id.sale_truck', string='Sales Truck', track_visibility='onchange')
    sale_truck_material_ids = fields.Many2many('sale.truck.item', string="Product Material", related="product_tmpl_id.sale_truck_material_ids", readonly=False, track_visibility='onchange')
    reg_in_customer_stock_card = fields.Boolean(related='product_tmpl_id.reg_in_customer_stock_card', string='Customer Stock Card', default=False,track_visibility='onchange')