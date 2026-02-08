"""File Sale Credit Limit"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    """class inherit sale.order"""
    _inherit = 'sale.order'

    
    status_so = fields.Selection([('0', 'Normal'), ('1', 'Overdue'), ('2', 'Overlimit'), ('3', 'Overdue & Overlimit'), 
                    ('4', 'Blacklist')])
    street = fields.Char(related='partner_id.street')

    @api.depends('partner_id','partner_pricelist_id')
    def _set_status_so(self):
        print("_set_status_so")
        for sale in self:
            sale.status_so = '0'
            if sale.partner_pricelist_id.black_list == 'blacklist':
                sale.status_so = '4'
            elif sale.partner_pricelist_id.over_due == 'overdue':
                sale.status_so = '1'
            elif sale.partner_pricelist_id.remaining_limit < sale.amount_total:
                sale.status_so = '2'
            elif sale.partner_pricelist_id.over_due == 'overdue' and sale.partner_pricelist_id.remaining_limit < sale.amount_total:
                sale.status_so = '3'

class SaleOrderLine(models.Model):
    """class inherit sale.order.line"""
    _inherit = 'sale.order.line'

    qty_stock = fields.Float(compute="_get_stock")
    product_type = fields.Selection([
        ('consu', 'Consumable'),
        ('service', 'Service'),
        ('product', 'Storable Product'),
        ], related='product_id.type')

    @api.depends('product_id','order_id.warehouse_id')
    def _get_stock(self):
        for line in self.sudo():
            location = line.order_id.warehouse_id.lot_stock_id
            avaliable_qty = 0
            
            available_qty = line.with_context(dict(location=location.id)).product_id.free_qty
            # print(('::::', available_qty))
            line.qty_stock = available_qty

    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        # for rec in self:
        #     if not rec.order_id.warehouse_id:
        #         raise UserError(_('Please fill the warehouse before input data in order line'))
        return res

    def create_internal_transfer(self, picking_id, picking_type_id):
        if picking_type_id.automatic_internal_transfer:
            location_id = picking_type_id.default_location_src_id
            location_dest_id = picking_type_id.default_location_dest_id
            if not picking_id:
                picking_id = self.env['stock.picking'].create({
                    'picking_type_id': picking_type_id.id,
                    'location_id': location_id.id,
                    'location_dest_id': location_dest_id.id})
            self.env['stock.move'].create({
                'name': self.product_id.name,
                'product_id': self.product_id.id,
                'product_uom_qty': self.product_uom_qty - self.qty_stock,
                'product_uom': self.product_id.uom_id.id,
                'picking_id': picking_id.id,
                'location_id': location_id.id,
                'location_dest_id': location_dest_id.id})
        return picking_id
