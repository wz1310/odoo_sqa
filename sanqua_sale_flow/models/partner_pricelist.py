# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

class PartnerPricelist(models.Model):
    _inherit = 'partner.pricelist'


    @api.depends('team_id')
    def _compute_team_member_ids(self):
        for rec in self:
            rec.team_member_ids = rec.team_id.sales_user_ids.ids