# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class PickingReturnRequestLine(models.Model):
    _name = "picking.return.request.line"
    _description = "Line Return Barang"

    request_id = fields.Many2one('picking.return.request',string="Return Request", required=True)
    sale_line_id = fields.Many2one('sale.order.line', string="SO Line", required=True)
    product_id = fields.Many2one(string="Product", related="sale_line_id.product_id", store=True)
    lot_id = fields.Many2one('stock.production.lot', string="Lot/Serial Number", required=True)
    delivered_qty = fields.Float(string="Done", digits=dp.get_precision('Product Unit of Measure'), 
        related="sale_line_id.product_uom_qty", store=True)
    qty = fields.Float(string="Return Qty", required=True)

    @api.onchange('sale_line_id')
    def _onchange_sale_line_id(self):
        list_moveline_id = []
        res = {}
        self.lot_id = False
        stock_move = self.env['stock.move'].search([('sale_line_id','=',self.sale_line_id.id)])
        for each in stock_move.move_line_ids:
            list_moveline_id.append(each.lot_id.id)
        res['domain'] = {'lot_id':[('id','in',list_moveline_id)]}
        return res

    def _check_done_qty(self):
        self.ensure_one()
        if self.qty > self.delivered_qty :
            raise UserError(_("Return quantity cannot filled more than Done quantity!"))

    @api.onchange('qty')
    def _onchange_qty(self):
        self._check_done_qty()

    @api.constrains('qty')
    def _constrains_qty(self):
        for rec in self:
            rec._check_done_qty()