"""File sale order truck"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)

class SaleOrderTruckDispanser(models.Model):
    _name = "sale.order.truck.dispanser"
    _description = "Sale Order Truck Dispanser"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"


    
    name = fields.Char(related='sale_truck_id.name', string="Name", track_visibility='onchange')
    sale_truck_id = fields.Many2one('sale.order.truck', string="Sale Truck", ondelete="cascade", onupdate="cascade", track_visibility='onchange')
    plant_id = fields.Many2one('res.company', compute="_compute_sale_truck", track_visibility='onchange')
    warehouse_id = fields.Many2one('stock.warehouse', compute="_compute_sale_truck", track_visibility='onchange')

    product_id = fields.Many2one('product.product', string="Product", track_visibility='onchange')
    qty = fields.Float(digits=dp.get_precision('Qty Loaded'), default=0.0, track_visibility='onchange')
    uom_id = fields.Many2one(related='product_id.uom_id',string='Uom', required=True, track_visibility='onchange')
    return_qty = fields.Float(digits=dp.get_precision('product uom'), default=0.0, string='Returned Qty', track_visibility='onchange')
    sent_qty = fields.Float(digits=dp.get_precision('product uom'), default=0.0, string='Sent Qty', compute='_compute_sent_qty', track_visibility='onchange')
    truck_dispanser_line_ids = fields.One2many('sale.order.truck.dispanser.line','truck_dispanser_id', string='Dispanser Line', track_visibility='onchange')
    partner_ids = fields.Many2many(related='sale_truck_id.partner_ids', string='Customer', track_visibility='onchange')
    state = fields.Selection(related="sale_truck_id.state", string='State', track_visibility='onchange')
    serializable = fields.Boolean(string='Serializable', help="This serial number will used in Sale Truck.", track_visibility='onchange')
    lot_id = fields.Many2one('stock.production.lot', string='Lot/Serial Number', track_visibility='onchange')
    available_lot_ids = fields.Many2many('stock.production.lot', compute="_compute_available_lot_ids", string="Available Lots")

    @api.depends('sale_truck_id')
    def _compute_sale_truck(self):
        for rec in self:
            rec.update({'warehouse_id':rec.sale_truck_id.warehouse_id.id, 'plant_id':rec.sale_truck_id.plant_id.id})

    
    def _get_available_lot(self):
        Lots = self.env['stock.production.lot']
        if self.product_id.id and self.sale_truck_id.sudo().warehouse_id.id:
            target_company = self.sudo().plant_id
            # Lots = Lots.with_user(self.env.company.intercompany_user_id.id).with_context(force_company=target_company.id, allowed_company_ids=target_company.ids).search([('product_id','=',self.product_id.id)]).filtered(lambda r:r.product_qty>0.0)
            # AvailebleLots = Lots.with_user(self.env.company.intercompany_user_id.id).with_context(force_company=target_company.id, allowed_company_ids=target_company.ids).search([('product_id','=',self.product_id.id)])
            # print(self.product_id.stock_quant_ids)
            
            Lots = self.product_id.sudo().stock_quant_ids.filtered(lambda r:r.sudo().location_id.id==self.sale_truck_id.warehouse_id.sudo().lot_stock_id.id, r.sudo().quantity>0.0)
            Lots = Lots.mapped('lot_id')

        return Lots

    @api.depends('product_id','qty', 'warehouse_id')
    def _compute_available_lot_ids(self):
        for rec in self:
            Lots = rec._get_available_lot()
            rec.available_lot_ids = Lots.ids

    @api.onchange('product_id','qty')
    def _onchange_product(self):
        res = {}
        domain = {}
        is_true = self.product_id.id and self.sale_truck_id.id and self.sale_truck_id.sudo().warehouse_id.id
        
        if self.product_id.id:
            Lots = self._get_available_lot()
            domain.update({
                'lot_id':[('id','in',Lots.ids)]
            })
        if domain:
            res.update({'domain':domain})
        
        return res

    def action_show_details(self):
        self.ensure_one()
        view = self.env.ref('sales_truck.sale_order_truck_dispanser_view_form')
        return {
            'name': _('Customer Operations'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sale.order.truck.dispanser',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': dict(
                self.env.context,
                show_customer_ids= self.partner_ids.ids or []
            ),
        }

    def confirm(self):
        return {'type': 'ir.actions.act_window_close'}

    def _compute_sent_qty(self):
        for this in self:
            qty = 0
            for orderline in this.truck_dispanser_line_ids:
                qty=qty+orderline.qty
            this.update({'sent_qty': qty,})

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            if self.product_id.tracking == 'serial':
                self.serializable = True
                self.qty = 1.0
                return {'domain':{'lot_id':[('product_id','=',self.product_id.id),('company_id','=',self.sale_truck_id.plant_id.id)]}}
            else:
                self.serializable = False
                self.qty = 0.0