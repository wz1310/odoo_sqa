"""File sale order truck"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class ProductTemplate(models.Model):
    _inherit = "product.template"

    sale_truck = fields.Boolean(string='Sales Truck', default=False, help="This product will used in Sale truck", track_visibility='onchange')
    sale_truck_material_ids = fields.Many2many('sale.truck.item', string="Product Material", track_visibility='onchange')
    reg_in_customer_stock_card = fields.Boolean(string='Customer Stock Card', default=False,track_visibility='onchange')

    @api.constrains('sale_truck')
    def _constrains_sale_truck(self):
        for rec in self:
            if rec.sale_truck == False:
                rec.reg_in_customer_stock_card = False