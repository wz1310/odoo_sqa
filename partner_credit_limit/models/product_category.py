"""File Product Category"""
from ast import literal_eval
from odoo import api, fields, models, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.exceptions import UserError, ValidationError


class ProductCategory(models.Model):
    """ inherited product category object """
    _inherit = "product.category"

    fixed_discount = fields.Float('Discount (Rp)')
    percent_discount = fields.Char()
