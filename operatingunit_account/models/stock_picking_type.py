# -*- coding: utf-8 -*-
"""file stock_picking_type"""
from odoo import models, fields


class StockPickingType(models.Model):
    """inherit model stock picking type"""
    _inherit = 'stock.picking.type'

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    journal_id = fields.Many2one('account.journal', string='Journal')