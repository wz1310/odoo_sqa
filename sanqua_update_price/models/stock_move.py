# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round, float_is_zero

import logging
_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    #update price unit when create
    def _get_stock_move_price_unit_new(self):
        self.ensure_one()
        line = self[0]
        if line.product_id:
            price_unit = line.product_id.standard_price
        return price_unit
    
    @api.model
    def create(self, values):
        res = super(StockMove, self).create(values)
        if res.price_unit == 0.0:
            price_unit = res._get_stock_move_price_unit_new()
            res.update({'price_unit': price_unit})
        return res

    def update_price_in_stock_move(self, limit):
        move_ids_ids = self.env['stock.move'].search([('picking_code', '=', 'outgoing'),
                                                    ('price_unit', '=', 0.0)], limit=limit)
        for data in move_ids_ids:
            data.price_unit = data.product_id.standard_price
