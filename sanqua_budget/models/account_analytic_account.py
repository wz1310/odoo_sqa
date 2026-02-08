# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    purchase_order_line_ids = fields.One2many('purchase.order.line', 'account_analytic_id', string='Purchase Order Lines')