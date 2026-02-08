# -*- coding: utf-8 -*-
"""file account journal"""
from odoo import models, fields


class AccountJournal(models.Model):
    """inherit model Account Journal"""
    _inherit = 'account.journal'

    branch_id = fields.Many2one('res.branch', string='Operating Unit')
