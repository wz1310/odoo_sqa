# -*- coding: utf-8 -*-
"""file stock_picking"""
from odoo import models, fields, api


class StockPicking(models.Model):
    """inherit model stock picking"""
    _inherit = 'stock.picking'

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')

    @api.onchange('picking_type_id', 'partner_id')
    def onchange_picking_type(self):
        res = super(StockPicking, self).onchange_picking_type()
        self.analytic_account_id = self.picking_type_id.analytic_account_id.id
        return res
    
    # @api.multi
    def action_done(self):
        res = super(StockPicking, self).action_done()
        self.ensure_one()
        if self.sale_id and not self.analytic_account_id:
            self.analytic_account_id = self.picking_type_id.analytic_account_id.id
        if self.sale_id and (not self.sale_id.journal_id or not self.sale_id.analytic_account_id):
            self.sale_id.journal_id = self.picking_type_id.journal_id.id
            self.sale_id.analytic_account_id = self.picking_type_id.analytic_account_id.id
        return res