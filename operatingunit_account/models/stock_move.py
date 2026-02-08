# -*- coding: utf-8 -*-
"""file stock_move"""
from odoo import models


class StockMove(models.Model):
    """inherit model stock move"""
    _inherit = 'stock.move'

    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description):
        """ Overridden from stock_account to add analytic account
        """
        self.ensure_one()
        rslt = super(StockMove, self)._generate_valuation_lines_data(partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description)
        analytic_account = False
        if self.picking_id and self.picking_id.analytic_account_id:
            analytic_account = self.picking_id.analytic_account_id.id
        rslt['credit_line_vals']['analytic_account_id'] = analytic_account
        rslt['debit_line_vals']['analytic_account_id'] = analytic_account
        return rslt
