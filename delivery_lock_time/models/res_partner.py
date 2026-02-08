# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    delivery_lead_time = fields.Float(string='Delivery Lead Time', track_visibility='onchange', default=3.0)