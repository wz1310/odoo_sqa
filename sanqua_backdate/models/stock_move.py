# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.constrains('move_id', 'lot_id', 'product_id')
    def _constrains_lot_move_line(self):
        for data in self:
            count = 0
            if len(data.move_id) > 1:
                for move in data.move_id:
                    if move:
                        if move.production_id:
                            continue
                        else:
                            if data.lot_id and data.product_id and data.picking_id:
                                check_data = self.env['stock.move.line'].search([('move_id', '=', move.id),
                                                                    ('lot_id', '=', data.lot_id.id),
                                                                    ('product_id', '=', data.product_id.id)])
                                count = len(check_data)
            else:
                if data.move_id and data.move_id.production_id:
                    continue
                if data.move_id and data.lot_id and data.product_id and data.picking_id:
                    check_data = self.env['stock.move.line'].search([('move_id', '=', data.move_id.id),
                                                                    ('lot_id', '=', data.lot_id.id),
                                                                    ('product_id', '=', data.product_id.id)])
                    count = len(check_data)
            if count > 1:
                raise ValidationError(_('Cannot use same lot %s' % (data.lot_id.name)))
