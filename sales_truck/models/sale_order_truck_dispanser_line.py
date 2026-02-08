"""File sale order truck line"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp

class SaleOrderTruckDispanserLine(models.Model):
    _name = "sale.order.truck.dispanser.line"
    _description = "Sale Order Truck Dispanser Line"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"

    truck_dispanser_id = fields.Many2one('sale.order.truck.dispanser', string="Order Dispanser", ondelete="cascade", onupdate="cascade", required=True, track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, track_visibility='onchange')
    qty = fields.Float(string='Product Uom', digits=dp.get_precision('Product Uom'), default=0.0, track_visibility='onchange')
    uom_id = fields.Many2one(related='truck_dispanser_id.uom_id',string='Uom', track_visibility='onchange')
