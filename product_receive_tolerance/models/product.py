from odoo import models, fields, api

class ProductTemplate(models.Model):
    """inherit models Product Template for add new field"""
    _inherit = 'product.template'

    qty_tolerance = fields.Float(string="Allow Quantity Tolerance (%)",help="Percentage of product quantity tolerance",store=True)


class Product(models.Model):
    """inherit models res users for add new field"""
    _inherit = 'product.product'

    qty_tolerance = fields.Float(string="Allow Quantity Tolerance (%)",related="product_tmpl_id.qty_tolerance",help="Percentage of product quantity tolerance",store=True)
    