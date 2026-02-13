from datetime import datetime
import logging
import base64
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ProductProduct(models.Model):
    _inherit = 'product.template'

    @api.depends('name', 'default_code')
    def _compute_display_name(self):
        action = self.env.context.get('params', {}).get('action')
        print(action)
        # if action == 'sales':
        for template in self:
            # action = template.env.context.get('params', {}).get('action')
            # print(action)
            product = template.env['product.product'].search([('product_tmpl_id','in',[template.id])])
            on_hande = sum(product.mapped('qty_available'))
            if on_hande > 0:
                template.display_name = False if not template.name else (
                    '{}{}'.format(
                        template.default_code and '[%s] ' % template.default_code or '', template.name
                        ))
            else:
                template.display_name = False if not template.name else (
                    '{}{}'.format(
                        template.default_code and '⚠️ [%s] ' % template.default_code or '', template.name
                        ))
