# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError,UserError

_logger = logging.getLogger(__name__)

class ResPartnerCompetitor(models.Model):
    _inherit = 'res.partner.competitor'

    @api.model
    def create(self,vals):
        self._change_uppercase_char(vals)
        res = super(ResPartnerCompetitor,self).create(vals)
        if self._context.get('contact_change_request') == True:
            self.env['contact.change.request'].create_direct_form(res.id,self._context.get('request_id'),self._context.get('model_name'))
        return res

    # @api.model
    def write(self, vals):
        self._change_uppercase_char(vals)
        return super(ResPartnerCompetitor,self).write(vals)

    def _change_uppercase_char(self,vals):
        upper_list = ['brand','description','product_volume','external_customer']
        for k,v in vals.items():
            if k in upper_list:
                if v:
                    vals[k] = v.upper()

            