# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from odoo.tools.date_utils import start_of, end_of, add
from odoo.tools.misc import format_date


class Company(models.Model):
    _inherit = "res.company"

    mrp_mps_show_monthly = fields.Boolean('Montly', default=True)
    mrp_mps_show_weekly = fields.Boolean('Weekly', default=True)
    mrp_mps_show_daily = fields.Boolean('Daily', default=True)
