from datetime import datetime
import logging
import base64
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ProductProduct(models.Model):
    _inherit = 'product.template'

    @api.depends('name', 'default_code')
    def _compute_display_name(self):
        warehouse_id = self.env.context.get('warehouse_id_filter')
        print("warehouse",warehouse_id)
        # if action == 'sales':
        for template in self:
            product = template.env['product.product'].search([('product_tmpl_id','in',[template.id])]).with_context(warehouse_id=warehouse_id)
            on_hande = sum(product.mapped('qty_available'))
            print("qty", on_hande)
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