"""File sale order truck item"""
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp

class SaleTruckItem(models.Model):
    _name = "sale.truck.item"
    _description = "Sale Order Truck Item"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"

    name = fields.Char(string='Name', track_visibility='onchange')
    product_id = fields.Many2one('product.product', string='Product', track_visibility='onchange')
    product_tmpl_id = fields.Many2one(related='product_id.product_tmpl_id', string='Parent', store=True, track_visibility='onchange')
    qty = fields.Float(string='Quantity', digits=dp.get_precision('Quantity'), default=0.0, track_visibility='onchange')
    product_qty_master = fields.Float(string='Quantity Master', digits=dp.get_precision('Quantity'), default=1.0, track_visibility='onchange')
    uom_id = fields.Many2one(related='product_id.uom_id', string='Uom', track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='company', track_visibility='onchange', default=False)

    @api.onchange('product_id','qty')
    def _onchange_name_get(self):
        qty = int(self.qty or 0)
        if self.product_id and self.qty:
            self.name = self.product_id.name+' '+str(qty)+' '+self.uom_id.name
