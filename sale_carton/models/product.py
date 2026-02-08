# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductCategory(models.Model):
    _inherit = 'product.category'

    carton = fields.Boolean(string='Carton', default=False)