# -*- coding: utf-8 -*-
"""file sale order"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

class SaleOrder(models.Model):
    """inherit model Sale Order"""
    _inherit = 'sale.order'

    journal_id = fields.Many2one('account.journal', string='Journal')
