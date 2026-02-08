# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _

class MasterReasonQc(models.Model):
    _name = "master.reason.qc"
    _description = "Master Reason of QC"
    _order = 'name, id'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
