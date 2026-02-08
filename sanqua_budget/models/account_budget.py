# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CrossoveredBudget(models.Model):
    _inherit = 'crossovered.budget'

    asset_id = fields.Many2one('account.asset', string='Asset')
    purchase_ids = fields.Many2many('purchase.order', string='Purchase Order',compute='_compute_purchase_ids')

    def _compute_purchase_ids(self):
        for rec in self:
            res = False
            if len(rec.crossovered_budget_line) > 0:
               res = rec.crossovered_budget_line.mapped(lambda self: self.purchase_order_line_ids.mapped('order_id'))
            rec.purchase_ids = res

             
class CrossoveredBudgetLines(models.Model):
    _inherit = 'crossovered.budget.lines'

    purchase_order_line_ids = fields.One2many('purchase.order.line', related='analytic_account_id.purchase_order_line_ids', string='Purchase Order Lines')

    def _compute_percentage(self):
        for line in self:
            if line.planned_amount != 0.00:
                line.percentage = float((line.practical_amount or 0.0) / line.planned_amount)
            else:
                line.percentage = 0.00