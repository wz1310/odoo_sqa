# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    makloon = fields.Boolean(string='Makloon')

class ProductProduct(models.Model):
    _inherit = 'product.product'

    makloon = fields.Boolean(string='Makloon',related='product_tmpl_id.makloon')