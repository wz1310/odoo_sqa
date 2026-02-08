# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    customer_lead_time = fields.Float(string='Customer Lead Time', track_visibility='onchange', default=3.0)