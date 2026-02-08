# -*- coding: utf-8 -*-

import logging
from odoo.exceptions import ValidationError,UserError
from odoo import _, api, fields, models
from datetime import datetime

_logger = logging.getLogger(__name__)

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    @api.onchange('account_analytic_id','price_total')
    def _onchange_account_analytic_id(self):
        self._constrains_account_analytic_id()

    @api.constrains('account_analytic_id','price_total')
    def _constrains_account_analytic_id(self):
        for rec in self:
            if rec.account_analytic_id:
                crossovered_budget_line_id = rec.account_analytic_id.mapped(lambda self: self.crossovered_budget_line.filtered(lambda r: r.date_from <= fields.date.today() and r.date_to >= fields.date.today()))
                if crossovered_budget_line_id:
                    if all(crossovered_budget_line_id.mapped(lambda r: (r.practical_amount + rec.price_total) > r.planned_amount)):
                        raise UserError(_("This product amount is over budget."))
                else:
                    raise UserError(_("%s did not have any budget in range of date order at item %s.") % (rec.account_analytic_id.display_name, rec.product_id.display_name,))