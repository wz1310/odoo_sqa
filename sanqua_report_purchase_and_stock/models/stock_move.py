# -*- coding: utf-8 -*-
""" Customize Stock Move"""
from odoo import api, fields, models


class StockMove(models.Model):
    """ Inherit stock move"""

    _inherit = "stock.move"

    difference_qty = fields.Float(compute='_compute_difference_qty', store=True)
    no_sj_vendor = fields.Char(related='picking_id.no_sj_vendor', string="No SJ Vendor", store=True)
    vendor_id = fields.Many2one('res.partner', related='picking_id.partner_id',string="Vendor", store=True)
    received_date_sj = fields.Datetime(related='picking_id.date_received', string="Received Date")
    
    
    
    @api.depends('product_uom_qty', 'quantity_done')
    def _compute_difference_qty(self):
        for data in self:
            data.difference_qty = data.product_uom_qty - data.quantity_done
