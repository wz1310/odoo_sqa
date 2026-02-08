"""File CRM Team"""
from odoo import api, fields, models, _


class ProductCategory(models.Model):
    """class inherit product.category"""
    _inherit = 'product.category'

    check_stock = fields.Boolean(default=False, copy=False, help="This configuration for confirm sale, if product less than stock will blocked")
