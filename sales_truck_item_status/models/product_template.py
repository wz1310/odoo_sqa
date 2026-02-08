"""File sale order truck"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class ProductTemplate(models.Model):
    _inherit = "product.template"

    sale_truck_dispenser = fields.Boolean(string='Dispenser', default=False, help="This product will used in Sale truck", track_visibility='onchange')
    # qty_field = fields.Selection([
    #     ('delivered_qty', 'Delivered'),
    #     ('difference_qty', 'Different')
    # ], string='Qty Computation Source',default='delivered_qty')

    # @api.constrains('reg_in_customer_stock_card')
    # def _constrains_reg_in_customer_stock_card(self):
    #     for rec in self:
    #         if rec.reg_in_customer_stock_card == False:
    #             rec.qty_field = 'delivered_qty'