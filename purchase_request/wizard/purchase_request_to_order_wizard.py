from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta

import logging
_logger = logging.getLogger(__name__)

class PurchaseRequestToOrder(models.TransientModel):
    _name = 'purchase.request.to.order'
    _description = 'Purchase Request To Order'

    def _default_request_id(self):
       return self.env.context.get('_default_request_id')

    request_id = fields.Many2one('purchase.request', string='Request',required=True,default=_default_request_id)
    line_ids = fields.One2many('purchase.request.to.order.line','wizard_id', string='Items')
    supplier_id = fields.Many2one('res.partner', string='Supplier',domain="[('supplier','=',True)]",required=True)
    is_asset = fields.Boolean(related="request_id.is_asset", readonly=True)

    @api.onchange('request_id')
    def _onchange_request_id(self):
        line_ids = [(5,)]
        for line in self.request_id.line_ids:
            qty = line.qty - line.qty_released
            if qty>0:
                line_ids.append((0,0, {
                    'wizard_id': self.id,
                    'item_id':line.id,
                    'qty':qty
                }))
        self.line_ids = line_ids

    def validate_non_asset_type(self):
        self.ensure_one()
        non_asset_type = self.line_ids.mapped('non_asset_type')
        if non_asset_type and any(non_asset_type) and len(non_asset_type)>1:
            unique_non_asset = list(set(non_asset_type))
            if len(unique_non_asset)>1:
                raise UserError(_("Can't confirming different non asset types in 1 form!\nTry Confirming %s items") % (", ".join(non_asset_type)))
    
    def btn_confirm(self):
        # self.validate_non_asset_type()
        for line in self.line_ids:
            line.item_id._valid_to_po()
            line.validity_qty()
            
        purchase_id = self.env['purchase.order'].create({
                                'partner_id':self.supplier_id.id,
                                'user_id': self.request_id.user_id.id,
                                'asset' : self.request_id.is_asset,
                                'purchase_order_type' : self.request_id.purchase_order_type
                            })
        if purchase_id:
            vals = []
            for line in self.line_ids:
                data = {
                    'product_id': line.item_id.product_id.id,
                    'name' : line.item_id.product_id.display_name,
                    'product_qty': line.qty,
                    'product_uom' : line.uom_id.id,
                    'price_unit' : line.item_id.product_id.lst_price,
                    'order_id': purchase_id.id,
                    'date_planned': fields.Date.from_string(purchase_id.date_order),
                    'purchase_request_line_id' : line.item_id.id,
                }
                vals.append(data)
        new_po = self.env['purchase.order.line'].with_context(active_model='purchase.requisition').create(vals)
        
        form = self.env.ref('purchase.purchase_order_form')
        context = dict(self.env.context or {})
        # context.update({}) #uncomment if need append context
        res = {
            'name': "%s - %s" % (_('Purchase Order - '), self.request_id.name),
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'view_id': form.id,
            'views':[(form.id,'form')],
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'current',
            'res_id':purchase_id.id,
            'res_ids':purchase_id.ids,
        }
        return res

class PurchaseRequestToOrderLine(models.TransientModel):
    _name = 'purchase.request.to.order.line'
    _description = 'Purchase Request To Order Line'

    wizard_id = fields.Many2one('purchase.request.to.order', string='Wizard')
    request_id = fields.Many2one(related='wizard_id.request_id')
    item_id = fields.Many2one('purchase.request.line', string='Product',domain=[])
    qty = fields.Float(string='Qty', digits="Product of Measure",required=True)
    qty_released = fields.Float(string='Qty Released', digits="Product Unit Of Measure",related='item_id.qty_released')
    uom_id = fields.Many2one(string='UOM',related='item_id.uom_id')
    is_asset = fields.Boolean(related="item_id.is_asset")
    non_asset_type = fields.Selection(related="item_id.non_asset_type")

    def validity_qty(self):
        if (self.qty_released + self.qty) > self.item_id.qty:
            raise UserError(_("Demand = %s, Released Qty = %s\nCan't confirm more than demand!" % (self.qty,self.qty_released))) 