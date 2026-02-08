"""File sale order truck line"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)

class SaleOrderMaterial(models.Model):
    _name = "sale.order.truck.material"
    _description = "Sale Order Truck material"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"

    sale_truck_id = fields.Many2one('sale.order.truck', string="Order Truck", ondelete="cascade", onupdate="cascade", required=True, track_visibility='onchange')
    sale_truck_line_id = fields.Many2one('sale.order.truck.line', string="Order Truck Line", ondelete="cascade", onupdate="cascade", required=False, track_visibility='onchange')
    partner_id = fields.Many2one('res.partner',compute='_compute_partner_id', inverse="_inverse_true",track_visibility='onchange', store=True)
    product_id = fields.Many2one('product.product', string="Product", required=True, track_visibility='onchange')
    product_tracking = fields.Selection(related="product_id.tracking", readonly=True)
    product_uom_qty = fields.Float(string='Qty', digits=dp.get_precision('Product Uom'), default=0.0, track_visibility='onchange')
    uom_id = fields.Many2one(related='product_id.uom_id',string='Uom', required=True, track_visibility='onchange')
    delivered_qty = fields.Float(string='Delivered Qty', track_visibility='onchange', compute="_compute_report_qty", store=True, inverse="_inverse_true")
    rejected_qty = fields.Float(string='Rejected Qty', track_visibility='onchange', compute="_compute_report_qty", store=True, inverse="_inverse_true")
    return_qty = fields.Float(string='Return Qty', track_visibility='onchange', compute="_compute_report_qty", store=True, inverse="_inverse_true")
    different_qty = fields.Float(string='Order Different', track_visibility='onchange')
    state = fields.Selection(related="sale_truck_id.state", string='State', track_visibility='onchange')
    non_sanqua = fields.Boolean(string='Return',default=False,track_visibility='onchange')
    receive_material = fields.Boolean('Receiving', related="sale_truck_id.receive_material", readonly=True, help="Check if only receiving material")

    def _inverse_true(self):
        return True


    @api.depends('lot_ids.rejected_qty','lot_ids.delivered_qty')
    def _compute_report_qty(self):
        for rec in self:
            rec.update({
                'delivered_qty':sum(rec.lot_ids.mapped('delivered_qty')),
                'rejected_qty':sum(rec.lot_ids.mapped('rejected_qty')),
                'return_qty':sum(rec.lot_ids.mapped('return_qty'))
            })

    def _check_qty_product(self):
        location_id = self.sale_truck_id.sudo().warehouse_id.lot_stock_id
        self = self.sudo().with_context(location=location_id.id,force_company=self.sale_truck_id.plant_id.id,allowed_company_ids=self.sale_truck_id.plant_id.ids)
        qty_available = self.product_id.qty_available
        if self.product_uom_qty > qty_available:
            raise UserError(_('Stock quantities for product %s not available on this location!') % (self.product_id.display_name))


    def _check_balance(self):
        
        msgs = []
        # only has sale_truck_line_id
        self = self.filtered(lambda r:r.sale_truck_line_id.id)
        # if self.product_tracking!='none':
        #     self.reccompute_lot_qty()

        material_not_balanced = self.filtered(lambda r:r.state not in ['draft','submited','rejected','waiting_approval'] and r.product_uom_qty != (r.delivered_qty+r.rejected_qty))
        if len(material_not_balanced):
            msgs.append("%s" % ("\n".join(material_not_balanced.mapped(lambda r:"%s - %s" % (r.product_id.display_name, r.partner_id.display_name,))),))

        if len(msgs):
            raise UserError(_("Qty not balance on Materials, please check:\n%s") % ("\n".join(msgs),))
    

    def _inverse_true(self):
        for rec in self:
            print('>>>>>', rec.partner_id)

    lot_ids = fields.One2many('sale.order.truck.material.lot', 'material_id', string="Lots")



    @api.onchange('delivered_qty','rejected_qty')
    def onchange_different_qty(self):
        total_qty = self.delivered_qty + self.rejected_qty
        different_qty = self.product_uom_qty - total_qty
        self.different_qty = different_qty

    def _check_lot_duplicate(self):
        self.ensure_one()
        lots = self.lot_ids.mapped('lot_id')
        for lot in lots:
            
            counter = len(self.lot_ids.filtered(lambda r:r.lot_id.id==lot.id))
            
            if counter>1:
                raise UserError(_("Can't add duplicates lot.\n\nPlease Check Lot %s!") % (lot.display_name,))


    def _constrains_product_uom_qty(self):
        for rec in self:
            if rec.product_tracking!='none':
                # check lot_ids
                qty = sum(rec.lot_ids.mapped('product_uom_qty'))
                if rec.product_uom_qty and qty != rec.product_uom_qty:
                    raise UserError(_("Please select for %s %s of %s") % (rec.product_uom_qty, rec.uom_id.display_name, rec.product_id.display_name,))
    

    def btn_save(self):
        self.ensure_one()
        # check duplicate

        self._check_lot_duplicate()
        self._constrains_product_uom_qty()
        # self._check_balance()

        return {'type': 'ir.actions.act_window_close'}

    def write(self, vals):
        if len(self)==1:
            if self.state=='confirmed' and self.receive_material==True:
                # cant edit some fields
                unsets_fields = ['product_uom_qty','product_id','partner_id', 'delivered_qty', 'rejected_qty']
                for field in unsets_fields:
                    if vals.get(field):
                        del(vals[field])
        res = super().write(vals)
        self.btn_save()
        return res

    @api.depends('sale_truck_line_id')
    def _compute_partner_id(self):
        for rec in self:
            if rec.sale_truck_line_id:
                rec.partner_id = rec.sale_truck_line_id.partner_id
            else:
                rec.partner_id = False

    @api.onchange('sale_truck_id')
    def onchange_sale_truck_id(self):
        print(self._context)
        receive_material = self._context.get('default_receive_material')
        if receive_material:
            res = {
                'domain':{
                    'partner_id':[('customer','=',True), ('state','=','approved')]
                }
            }
        else:
            res = {
                'domain':{
                    'partner_id': [('id','in',self.sale_truck_id.order_line_ids.mapped('partner_id').ids)],
                }
            }
        return res

    def btn_delete_non_sanqua(self):
        return self.filtered(lambda r:r.non_sanqua).sudo().unlink()


class SaleOrderMaterialLot(models.Model):
    _name = 'sale.order.truck.material.lot'
    _description = 'sale.order.truck.material.lot'

    material_id = fields.Many2one('sale.order.truck.material', string="Material", required=True, ondelete="cascade", onupdate="cascade")
    product_id = fields.Many2one('product.product', related="material_id.product_id", readonly=True)
    product_tracking = fields.Selection(related="product_id.tracking", readonly=True)
    lot_id = fields.Many2one('stock.production.lot', string="Lot", required=True)

    product_uom_qty = fields.Float(string='Qty', digits=dp.get_precision('Product Uom'), default=0.0, track_visibility='onchange')
    delivered_qty = fields.Float(string='Order Delivered', track_visibility='onchange')
    rejected_qty = fields.Float(string='Order Rejected', track_visibility='onchange')
    return_qty = fields.Float(string='Return Qty', track_visibility='onchange')
    different_qty = fields.Float(string='Order Different', track_visibility='onchange')
    company_id = fields.Many2one('res.company', string="Company", compute=False, default=lambda self:self.env.company.id)
    state = fields.Selection(related="material_id.state", readonly=True)
    non_sanqua = fields.Boolean(string='Return', related="material_id.non_sanqua", readonly=True)

    def unlink(self):
        for rec in self:
            if rec.state not in ['draft','submited']:
                raise UserError(_("Can't deleting record!"))

    @api.onchange('lot_id')
    def _onchange_lot(self):
        res = 0.0
        if self.product_id.id and self.product_tracking == 'serial' and self.lot_id.id:
            if self.state == 'submited':
                if self.non_sanqua==True:
                    self.return_qty = 1.0
                else:
                    res = 1.0
        self.product_uom_qty = res

    @api.onchange('product_uom_qty')
    def _onchange_qty(self):
        res = 0.0
        if self.product_id.id and self.product_tracking == 'serial':
            if self.non_sanqua==True:
                self.return_qty = 1.0
            else:
                res = 1.0 # always 1
                self.product_uom_qty = res
        
    