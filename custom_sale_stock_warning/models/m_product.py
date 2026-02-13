from datetime import datetime
import logging
import base64
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ProductProduct(models.Model):
    _inherit = 'product.template'

    # def name_get(self):
    #     print("ahaaaaaaaaaaaaaaaa")
    #     result = []
    #     for product in self:
    #         stok = product.qty_available
    #         name = f"{product.display_name} (Stok: {stok})"
    #         if stok <= 0:
    #             name = f"⚠️ {product.display_name} (HABIS)"
    #         result.append((product.id, name))
    #     return result

    @api.depends('name', 'default_code')
    def _compute_display_name(self):
        action = self.env.context.get('params', {}).get('action')
        print(action)
        # if action == 'sales':
        for template in self:
            # action = template.env.context.get('params', {}).get('action')
            # print(action)
            product = template.env['product.product'].browse(template.id)
            print(product.name)
            template.display_name = False if not template.name else (
                '{}{}'.format(
                    template.default_code and '[%s] ' % template.default_code or '', template.name
                    ))