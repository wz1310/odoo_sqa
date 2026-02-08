# -*- encoding: utf-8 -*-
from odoo import fields, models, api, _

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    promotion_line_id = fields.Many2one('sale.order.promotion.line',string="Sale Order Promotion Line")