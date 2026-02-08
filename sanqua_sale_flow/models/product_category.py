from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProductCategory(models.Model):
    _inherit = 'product.category'

    finish_good = fields.Boolean(string='Finish Good')
    report_category = fields.Selection([
        ('sqa', 'SanQua'),
        ('btv', 'Batavia'),
        ('bvg', 'Beverage'),
        ('vit', 'VIT'),
        ('gln', 'Galon')
    ], string='Report Category')