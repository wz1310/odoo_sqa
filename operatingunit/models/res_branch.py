# -*- coding: utf-8 -*-
"""Res Branch"""
from odoo import models, fields


class ResBranch(models.Model):
    """new models res branch"""
    _name = 'res.branch'
    _description = 'This Module for configuration of Branch'

    name = fields.Char('Name')
    code = fields.Char('Code')
    active = fields.Boolean('Active', default=True)
    #partner = fields.Many2one('res.partner', 'Partner')
