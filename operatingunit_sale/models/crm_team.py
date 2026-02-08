# -*- coding: utf-8 -*-
"""file crm team"""
from odoo import models, fields


class CrmTeam(models.Model):
    """inherit model Sales Teams"""
    _inherit = 'crm.team'

    branch_id = fields.Many2one('res.branch', string='Operating Unit')
