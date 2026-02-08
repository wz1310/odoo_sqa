# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = 'res.company'

    rejection_location = fields.Many2one('stock.location', string="Rejection Location")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    rejection_location = fields.Many2one('stock.location', string='Rejection Location')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        
        res.update({'rejection_location':self.env.company.rejection_location.id})
        return res

    
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.company_id.write({'rejection_location':self.rejection_location.id})
