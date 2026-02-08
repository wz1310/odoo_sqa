"""File sale order truck line"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError
from odoo.addons import decimal_precision as dp
import math

class SaleOrderTruck(models.Model):
    _name = "sale.order.truck.line"
    _description = "Sale Order Truck Line"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"

    sale_truck_id = fields.Many2one('sale.order.truck', string="Order Truck", ondelete="cascade", onupdate="cascade", required=True, track_visibility='onchange')
    sale_truck_material_ids = fields.One2many('sale.order.truck.material', 'sale_truck_line_id', string="Material", track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, track_visibility='onchange', domain=[('customer','=',True)])
    product_id = fields.Many2one('product.product', string="Product", required=True, track_visibility='onchange')
    product_uom_qty = fields.Float(string='Qty', digits=dp.get_precision('Product Uom'), default=0.0, track_visibility='onchange')
    uom_id = fields.Many2one(related='product_id.uom_id',string='Uom', required=True, track_visibility='onchange')
    delivered_qty = fields.Float(string='Delivered', track_visibility='onchange',compute="_compute_report_qty", store=True, inverse="_inverse_true")
    rejected_qty = fields.Float(string='Rejected', track_visibility='onchange',compute="_compute_report_qty", store=True, inverse="_inverse_true")
    return_qty = fields.Float(string='Return Qty', track_visibility='onchange', compute="_compute_report_qty", store=True, inverse="_inverse_true")
    different_qty = fields.Float(string='Order Different', track_visibility='onchange')
    ##DION##
    is_overdue = fields.Boolean('Overdue',compute="_check_od_ol",default=False)
    is_overlimit = fields.Boolean('Overlimit',compute="_check_od_ol",default=False)

    approved_qty = fields.Float(string='Delivered', track_visibility='onchange')

    state = fields.Selection(related="sale_truck_id.state", string='State', track_visibility='onchange')
    partner_pricelist_id = fields.Many2one('partner.pricelist',compute='_compute_partner_pricelist_id', string='Partner Pricelist',track_visibility='onchange')
    pricelist_id = fields.Many2one('product.pricelist',related='partner_pricelist_id.pricelist_id', string='Pricelist',track_visibility='onchange')
    price_unit = fields.Monetary(string='Unit Price', track_visibility='onchange', compute="_compute_partner_pricelist_id", store=True)
    tax_ids = fields.Many2many('account.tax', string='Taxes',domain=[('active', '=', True)],track_visibility='onchange')
    discount_fixed_line = fields.Monetary(string='Discount (Rp)')
    price_subtotal = fields.Monetary(compute='_compute_amount',string='Subtotal',readonly=True,store=True,track_visibility='onchange')
    price_total = fields.Monetary(compute='_compute_amount',string='Total',readonly=True,store=True,track_visibility='onchange')
    price_tax = fields.Float(compute='_compute_amount', string='Total Tax', readonly=True, store=True,track_visibility='onchange')
    currency_id = fields.Many2one('res.currency',related='sale_truck_id.currency_id' , string='Currency',track_visibility='onchange')
    lot_ids = fields.One2many('sale.order.truck.line.lot', 'line_id', string='')
    product_tracking = fields.Selection(related="product_id.tracking", readonly=True)

    qty_editable = fields.Boolean(string="Qty Editable", compute="_compute_qty_editable", default=True)
    note = fields.Text(string='Note', track_visibility='onchange')

    def _update_approve_qty(self):
        for rec in self:
            rec.approved_qty = rec.product_uom_qty

    @api.depends('state')
    def _compute_qty_editable(self):
        for rec in self:
            res = False
            if rec.state == 'draft' or rec.state==False:
                res = True
            elif rec.state == 'submited' and self.user_has_groups('sales_truck.group_sale_truck_inventory_user'):
                res = True
            rec.qty_editable = res

    def _check_qty_product(self):
        location_id = self.sale_truck_id.sudo().warehouse_id.lot_stock_id
        self = self.sudo().with_context(location=location_id.id,force_company=self.sale_truck_id.plant_id.id,allowed_company_ids=self.sale_truck_id.plant_id.ids)
        qty_available = self.product_id.qty_available
        if self.product_uom_qty > qty_available:
            raise UserError(_('Stock quantities for product %s not available on this location!') % (self.product_id.display_name))
            

        if self.lot_ids:
            not_enoughlot = []
            for lot in self.lot_ids:
                newctx = self.env['product.product'].sudo() \
                    .with_context(location=location_id.id,
                        force_company=self.sale_truck_id.plant_id.id,
                        allowed_company_ids=self.sale_truck_id.plant_id.ids, lot_id=lot.lot_id.id)
                searchp = newctx.search([('id','=',self.product_id.id)])
                if searchp.qty_available < lot.product_uom_qty:
                    not_enoughlot.append("Lot %s tidak mencukupi. Permintaan: %s, Stock: %s" % (lot.lot_id.display_name, lot.product_uom_qty, searchp.qty_available,))
            if len(not_enoughlot):
                raise UserError("\n".join(not_enoughlot))


    @api.depends('partner_id','price_total')
    def _check_od_ol(self):
        for rec in self:
            pricelist = rec.partner_id.sudo().partner_pricelist_ids.filtered(lambda r:r.sudo().team_id.id==rec.sudo().sale_truck_id.team_id.id).sorted('id', reverse=True)
            if len(pricelist) > 0:
                pricelist = pricelist[0].sudo()
                if pricelist.over_due == 'overdue':
                    rec.is_overdue = True
                    rec.is_overlimit = False
                elif pricelist.remaining_limit < rec.price_total:
                    rec.is_overlimit = True
                    rec.is_overdue = False
                else:
                    rec.is_overlimit = False
                    rec.is_overdue = False
            else:
                rec.is_overdue = False
                rec.is_overlimit = False


    @api.depends('lot_ids.rejected_qty','lot_ids.delivered_qty')
    def _compute_report_qty(self):
        for rec in self:
            rec.update({
                'delivered_qty':sum(rec.lot_ids.mapped('delivered_qty')),
                'rejected_qty':sum(rec.lot_ids.mapped('rejected_qty')),
                'return_qty':sum(rec.lot_ids.mapped('return_qty'))
            })

    def _inverse_true(self):
        return True
    
    @api.depends('product_id')
    def _compute_partner_pricelist_id(self):
        for rec in self:
            if rec.product_id and rec.partner_id:
                partner_pricelist_id = rec.partner_id.partner_pricelist_ids.filtered(lambda r: r.team_id == rec.sale_truck_id.team_id)
                partner_pricelist_id = partner_pricelist_id.sudo()
                rec.partner_pricelist_id = partner_pricelist_id.sudo().id
                if partner_pricelist_id.pricelist_id:
                    if rec.product_id in partner_pricelist_id.pricelist_id.item_ids.mapped('product_id'):
                        rec.price_unit = partner_pricelist_id.pricelist_id.get_product_price(rec.product_id, rec.product_uom_qty, False)
                        rec.tax_ids = rec.product_id.taxes_id
                    else:
                        raise UserError(_('Product %s not defined in pricelist %s') % (rec.product_id.display_name,partner_pricelist_id.pricelist_id.display_name))
                else:
                    raise UserError(_('Please defined pricelist for %s in %s Division!') % (rec.sale_truck_id.sudo().team_id.display_name, rec.sudo().partner_id.display_name))
            else:
                rec.partner_pricelist_id = False

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id.id:
            self.partner_id.check_partner_pricelist(self.sale_truck_id.team_id)

    
    @api.constrains('partner_id')
    def _constrains_partner_id(self):
        for rec in self:
            rec.partner_id.check_partner_pricelist(rec.sale_truck_id.team_id)

    @api.onchange('delivered_qty', 'rejected_qty')
    def _onchange_material_qty(self):
        if self.product_id.sale_truck_material_ids and self.sale_truck_material_ids:
            material = self.env['sale.order.truck.material'].browse(self.sale_truck_material_ids.ids)
            for this in material:
                qty_deliver = self.delivered_qty
                qty_rejected = self.rejected_qty
                prod_material = self.product_id.sale_truck_material_ids
                prod = prod_material.filtered(lambda x : x.product_id.id == this.product_id.id)
                if prod:
                    this.delivered_qty = math.ceil(qty_deliver / prod.product_qty_master)
                    this.rejected_qty = math.ceil(qty_rejected / prod.product_qty_master)
                
                total_qty = this.delivered_qty + this.rejected_qty
                this.different_qty = math.ceil(this.product_uom_qty - total_qty)
    

    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):
        if self.state=='submited':
            if not self.approved_qty:
                self.approved_qty = self.product_uom_qty
            
            if self.product_uom_qty>self.approved_qty:
                
                raise ValidationError(_("can't change qty more than %s") % (self.approved_qty,))
        if self.product_id.sale_truck_material_ids and self.sale_truck_material_ids:
            material = self.env['sale.order.truck.material'].browse(self.sale_truck_material_ids.ids)
            for this in material:
                truck_item  = self.product_id.sale_truck_material_ids.filtered(lambda r:r.product_id.id==this.product_id.id)

                this.product_uom_qty = float(math.ceil(self.product_uom_qty / truck_item.product_qty_master))
                

    @api.depends('product_uom_qty', 'price_unit', 'tax_ids')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (0.0) / 100.0)
            taxes = line.tax_ids.compute_all(price, line.currency_id, line.product_uom_qty, product=line.product_id, partner=line.partner_id)
            disc_total = line.discount_fixed_line * line.product_uom_qty
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'] - disc_total,
                'price_subtotal': taxes['total_excluded'] - disc_total,
            })

    @api.onchange('delivered_qty','rejected_qty')
    def onchange_different_qty(self):
        total_qty = self.delivered_qty + self.rejected_qty
        different_qty = self.product_uom_qty - total_qty
        self.different_qty = different_qty
        self._check_lot_duplicate()
        self._constrains_product_uom_qty()
        # self._check_balance()

    def _check_lot_duplicate(self):
        # self.ensure_one()
        lots = self.lot_ids.mapped('lot_id')
        for lot in lots:
            counter = len(self.lot_ids.filtered(lambda r:r.lot_id.id==lot.id))
            if counter>1:
                raise UserError(_("Can't add duplicates lot.\n\nPlease Check Lot %s!") % (lot.display_name,))

    def _check_balance(self):
        
        msgs = []
        # only has sale_truck_line_id
        # self = self.filtered(lambda r:r.sale_truck_line_id.id)
        # if self.product_tracking!='none':
        #     self.reccompute_lot_qty()

        line_not_balanced = self.filtered(lambda r:r.state not in ['draft','rejected','waiting_approval'] and r.product_uom_qty != (r.delivered_qty+r.rejected_qty))
        if len(line_not_balanced):
            msgs.append("%s" % ("\n".join(line_not_balanced.mapped(lambda r:"%s - %s" % (r.product_id.display_name, r.partner_id.display_name,))),))
        if len(msgs):
            raise UserError(_("Qty not balance on Order, please check:\n%s") % ("\n".join(msgs),))

    def _constrains_product_uom_qty(self):
        for rec in self:
            if rec.product_tracking!='none':
                # check lot_ids
                qty = sum(rec.lot_ids.mapped('product_uom_qty'))
                if rec.product_uom_qty and qty != rec.product_uom_qty:
                    raise UserError(_("Qty tidak valid, permintaan = %s %s of %s, disiapkan=%s untuk customer=%s") % (rec.product_uom_qty, rec.uom_id.display_name, rec.product_id.display_name, qty,rec.partner_id.display_name))
    
    def check_lot_uom_qty(self):
        self._constrains_product_uom_qty()

class SaleOrderLineLot(models.Model):
    _name = 'sale.order.truck.line.lot'
    _description = 'sale.order.truck.line.lot'

    line_id = fields.Many2one('sale.order.truck.line', string="Material", required=True, ondelete="cascade", onupdate="cascade")
    product_id = fields.Many2one('product.product', related="line_id.product_id", readonly=True)
    product_tracking = fields.Selection(related="product_id.tracking", readonly=True)
    lot_id = fields.Many2one('stock.production.lot', string="Lot", required=True)

    product_uom_qty = fields.Float(string='Qty', digits=dp.get_precision('Product Uom'), default=0.0, track_visibility='onchange')
    delivered_qty = fields.Float(string='Order Delivered', track_visibility='onchange')
    rejected_qty = fields.Float(string='Order Rejected', track_visibility='onchange')
    return_qty = fields.Float(string='Return Qty', track_visibility='onchange')
    different_qty = fields.Float(string='Order Different', track_visibility='onchange')
    company_id = fields.Many2one('res.company', string="Company", compute=False, default=lambda self:self.env.company.id)
    state = fields.Selection(related="line_id.state", readonly=True)
    available_lot_in_location = fields.Many2many('stock.production.lot', compute="_check_available_lot", string="Available Lot", context={'all_companies':True})
    free_qty = fields.Float('Free To Use Quantity')


    def _get_lot_free_qty(self):
        self.ensure_one()
        # context = self._context.copy()
        # context.update({'allowed_company_ids':self.allowed_company_ids.ids, 'lot_id':self.lot_id.id})
        quant = self.env['stock.quant'].search([('product_id', '=', self.product_id.id),
                                            ('location_id', '=', self.line_id.sale_truck_id.warehouse_id.lot_stock_id.id),
                                            ('lot_id', '=', self.lot_id.id)])
        res = quant.quantity
        return res


    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        for rec in self:
            res = 0.0
            if rec.lot_id.id:
                res = rec._get_lot_free_qty()
            rec.free_qty = res

    @api.depends('line_id','product_id')
    def _check_available_lot(self):
		
        Lot = self.env['stock.production.lot']

        for rec in self.sudo():
            
            context = dict(force_company=rec.line_id.sale_truck_id.warehouse_id.company_id.id, allowed_company_ids=rec.line_id.sale_truck_id.warehouse_id.company_id.ids)
            ProductLot = Lot.with_user(rec.line_id.sale_truck_id.company_id.intercompany_user_id.id).with_context(context).search([('product_id','=',rec.product_id.id), ('company_id','=',rec.line_id.sale_truck_id.warehouse_id.company_id.id)])
            AvailableLot = self.env['stock.production.lot'].with_context(context)
            ProductProduct = self.env['product.product'].search([('id','in',ProductLot.mapped('product_id.id'))])
            quant_ids = self.env['stock.quant'].search([('product_id', '=', rec.product_id.id),
                                                        ('location_id', '=', rec.line_id.sale_truck_id.warehouse_id.lot_stock_id.id)])
            for quant in quant_ids:
                available = quant.quantity
                if available > 0.0:
                    AvailableLot += quant.lot_id

            rec.update({
                'available_lot_in_location':[(6,None, AvailableLot.ids)]
                })

    def unlink(self):
        for rec in self:
            if rec.state not in ['draft','submited']:
                raise UserError(_("Can't deleting record!"))

    @api.onchange('lot_id')
    def _onchange_lot(self):
        res = 0.0
        if self.product_id.id and self.product_tracking == 'serial' and self.lot_id.id:
            if self.state == 'submited':
                res = 1.0
        self.product_uom_qty = res

    @api.onchange('product_uom_qty')
    def _onchange_qty(self):
        res = 0.0
        if self.product_id.id and self.product_tracking == 'serial':
            res = 1.0 # always 1
            self.product_uom_qty = res