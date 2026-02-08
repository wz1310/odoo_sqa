# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp

class StockPickingSubstituteLine(models.TransientModel):
    _name = "stock.picking.substitute.line"

    substitute_id = fields.Many2one(
        'stock.picking.substitute',
        string="Stock Picking Substitute",
        required=False)
    move_id = fields.Many2one(
        'stock.move',
        string="Stock Move",
        required=True)
    product_id = fields.Many2one(
        'product.product',
        string="Substitute Item",
        required=True)
    qty = fields.Float(
        string="Quantity", 
        required=True, 
        digits=dp.get_precision('Product Unit of Measure'))

    # _sql_constraints = [(
    #     'substitute_product_uniq', 
    #     'unique (move_id)',
    #     'Duplicate products in substitute line not allowed !')]