# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    applied_on = fields.Selection([
        ('3_global', 'All Products'),
        ('2_product_category', ' Product Category'),
        ('0_product_variant', 'Product Variant')], "Apply On",
        default='0_product_variant', required=True,
        help='Pricelist Item applicable on selected option')