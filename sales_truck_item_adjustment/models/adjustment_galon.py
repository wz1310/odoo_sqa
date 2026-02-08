from odoo import api, fields, models, _


class AdjustmentGalon(models.Model):
    _name = 'adjustment.galon'
    _description = 'Adjustment Galon'

    name = fields.Char(default='/')
    partner_id = fields.Many2one('res.partner', string="Customer")
    product_id = fields.Many2one('product.product', string="Product")
    delivery_date = fields.Date(string='Date')
    borrow_qty = fields.Float(string='Borrow')
    deposito_qty = fields.Float(string='Changed')

    @api.model
    def create(self, vals):
        if vals.get('name')=='/':
            sequence = self.env.ref('sales_truck_item_adjustment.sequence_adjustment_galon')
            vals.update({'name': sequence.next_by_id()})
        return super(AdjustmentGalon, self).create(vals)

