# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

class PartnerPricelist(models.Model):
    _inherit = 'partner.pricelist'

    company_id = fields.Many2one('res.company', string="Company",compute=False,required=True, default=lambda self:self.env.company.id)


    @api.depends('team_id')
    def _compute_company(self):
        for rec in self:
            rec.company_id = rec.team_id.company_id.id

    @api.model
    def create(self,vals):
        res = super(PartnerPricelist,self).create(vals)
        if self._context.get('contact_change_request') == True:
            self.env['contact.change.request'].create_direct_form(res.id,self._context.get('request_id'),self._context.get('model_name'))
        return res