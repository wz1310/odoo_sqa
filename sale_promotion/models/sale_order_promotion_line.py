# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class SaleOrderPromotionLine(models.Model):
    _name = "sale.order.promotion.line"
    _description = "Line Support Promotion"

    order_id = fields.Many2one('sale.order.promotion', string='Order Reference', required=True, ondelete='cascade', index=True, copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('needapproval', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ], related='order_id.state', string='Status', readonly=True, default='draft')
    product_id = fields.Many2one(
        'product.product', string='Product')
    product_uom_qty = fields.Float(string='Quantity', 
        digits='Product Unit of Measure', required=True, default=1.0,)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', related='product_id.uom_id', store=True)
