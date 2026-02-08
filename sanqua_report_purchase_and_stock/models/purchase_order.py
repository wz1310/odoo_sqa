# -*- coding: utf-8 -*-
""" Customize Purchase Order Line"""
from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    """ Inherit purchase order line"""

    _inherit = "purchase.order.line"

    difference_qty = fields.Float(compute='_compute_difference_qty', store=True)
    no_sj_vendor = fields.Text(string='No SJ Vendor', store=True, compute="_check_nosj")

    @api.depends('product_qty', 'qty_received', 'product_id')
    def _check_nosj(self):
        
        for line in self:
            no_sj = ''
            
            move_ids = self.env['stock.move'].search([('purchase_line_id','=', line.id),('state','=','done')])
            for mov in move_ids:
                sign = 1
                if mov.picking_id.picking_type_code == 'outgoing':
                    sign = -1
                if mov.no_sj_vendor:
                    no_sj += ('%s (%s)\n') % (mov.no_sj_vendor,sign * mov.quantity_done)
                elif mov.picking_id.no_sj_wim:
                    no_sj += ('%s (%s)\n') % (mov.picking_id.no_sj_wim,sign * mov.quantity_done)
            if len(no_sj) <= 1:
                no_sj = False
            line.no_sj_vendor = no_sj
    
    @api.depends('product_qty', 'qty_received')
    def _compute_difference_qty(self):
        for data in self:
            data.difference_qty = data.product_qty - data.qty_received
