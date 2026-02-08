"""File Account Payment"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    exp_date = fields.Integer(sting="Expired Date")
