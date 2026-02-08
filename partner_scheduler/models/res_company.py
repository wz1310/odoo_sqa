# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    auto_delete_partner = fields.Float(string='Auto Delete Partner in', track_visibility='onchange', default=10.0)
