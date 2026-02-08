# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _

class MasterReasonQcPicking(models.Model):
    _name = "master.reason.qc.picking"
    _description = "Master Reason of QC in Picking"
    _order = 'name, id'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
