# coding: utf-8
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)



class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.constrains('is_asset')
    def constrains_asset(self):
        for rec in self:
            if rec.is_asset==True:
                if rec.type not in ['product']:
                    rec.type = rec.type
                    # raise UserError(_("If this product as an asset so must require to storeable the product"))
                rec.non_asset_type = False #make sure always false if is_asset = True