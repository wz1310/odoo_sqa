# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MisInherProds(models.Model):
    _inherit = 'product.template'

    amdk_groups = fields.Many2one('mis.sku', string="SKU")
    stock_min_max_ids = fields.One2many('stock.min.max','prod_temp_id', string="Stock Min Max")


class StockMinMax(models.Model):
    _name = 'stock.min.max'

    stock_min = fields.Integer()
    stock_max = fields.Integer()
    company_id = fields.Many2one('res.company',default=lambda self: self.env.company)
    prod_temp_id = fields.Many2one('product.template')