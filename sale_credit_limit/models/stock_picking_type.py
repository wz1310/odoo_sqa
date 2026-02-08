"""File Stock Picking Type"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockPickingType(models.Model):
    """class inherit stock.picking.type"""
    _inherit = 'stock.picking.type'

    automatic_internal_transfer = fields.Boolean(default=False, copy=False)


