# -*- coding: utf-8 -*-
"""file stock_warehouse"""
from odoo import models, fields, api


class StockWarehouse(models.Model):
    """inherit model stock warehouse"""
    _inherit = 'stock.warehouse'

    branch_id = fields.Many2one('res.branch', string='Operating Unit')


class StockPicking(models.Model):
    
    _inherit = 'stock.picking'
    
    # @api.multi
    def action_confirm(self):
        self.mapped('package_level_ids').filtered(lambda pl: pl.state == 'draft' and not pl.move_ids)._generate_moves()
        # call `_action_confirm` on every draft move
        self.mapped('move_lines')\
            .filtered(lambda move: move.state == 'draft')\
            .sudo()._action_confirm()
        # call `_action_assign` on every confirmed move which location_id bypasses the reservation
        self.filtered(lambda picking: picking.location_id.usage in ('supplier', 'inventory', 'production') and picking.state == 'confirmed')\
            .sudo().mapped('move_lines')._action_assign()
        return True