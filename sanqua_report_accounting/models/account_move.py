# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    product_categ_id = fields.Many2one('product.category', related='product_id.categ_id', store=True)