# -*- coding: utf-8 -*-
""" Customize sale Order Line"""
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    """ Inherit sale order line"""

    _inherit = "sale.order.line"

    difference_qty = fields.Float(compute='_compute_difference_qty', store=True)

    @api.depends('product_uom_qty', 'qty_delivered')
    def _compute_difference_qty(self):
        for data in self:
            data.difference_qty = data.product_uom_qty - data.qty_delivered
