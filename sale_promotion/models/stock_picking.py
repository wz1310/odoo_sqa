# -*- encoding: utf-8 -*-
from odoo import fields, models, api, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sale_promotion_id = fields.Many2one(comodel_name='sale.order.promotion', ondelete='cascade')
