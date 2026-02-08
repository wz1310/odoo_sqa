# -*- encoding: utf-8 -*-
from odoo import fields, models, api, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    internal_customer = fields.Boolean(default=False)


    # @api.onchange('interna_customer')
    # def _onchange_interna_customer(self):
    #     if self.internal_customer == True:

    def checking_pricelist_ids(self):
        self.ensure_one()
        if self.internal_customer:
            pass
        else:
            return super().checking_pricelist_ids()