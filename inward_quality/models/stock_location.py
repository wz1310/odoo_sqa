# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _

class Location(models.Model):
    """ inherit stock.location"""
    _inherit = "stock.location"

    check_active = fields.Boolean(
        string='Quality Check',
        default=False,
        help='Check this field to enable quality check '
                'on picking with destination to this location.')
