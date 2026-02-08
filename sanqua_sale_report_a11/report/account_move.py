# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    amount_total_payment = fields.Monetary(compute='_compute_amount_total_payment', string='Payments',store=True)
    code_partner = fields.Char(related='partner_id.code', store=True, string="")

    @api.depends('amount_total','amount_residual')
    def _compute_amount_total_payment(self):
        for rec in self:
            rec.amount_total_payment = rec.amount_total - rec.amount_residual
