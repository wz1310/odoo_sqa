# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    rpm_id = fields.Many2one('mrp.rpm', string="RPM Reference")
