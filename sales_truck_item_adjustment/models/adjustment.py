from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class SalesTruckItemAdjustment(models.Model):
    _name = 'sales.truck.item.adjustment'
    # _inherit = 'sales.truck.item.adjustment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Sales Truck Item Adjustment'


    name = fields.Char(string="Doc Name", required=False, default='/', track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', string="Customer", required=False, track_visibility='onchange')
    final_stock = fields.Float(related='partner_id.final_stock',string='Final Stock')
    date_deposito = fields.Date(string='Date')
    adjustment_type = fields.Selection([
        ('borrow', 'Borrow'),
        ('change', 'Change'),
        ('deposit', 'Deposit'),
        ('returned', 'Returned'),
        ('to_bill', 'To Bill')
    ], required=True, string="Status", track_visibility='onchange')
    is_deposit = fields.Boolean(string='is Deposit?')
    adjustment_type_temp = fields.Selection([
        ('borrow', 'Borrow'),
        ('change', 'Change'),
        ('deposit', 'Deposit'),
        ('returned', 'Returned'),
        ('to_bill', 'To Bill')
    ], string="Status")

    qty = fields.Float(string="Adjustment Qty", track_visibility='onchange')
    qty_after = fields.Float(string="Qty After",compute='_compute_qty', track_visibility='onchange',store=True)
    state = fields.Selection([('draft','Draft'), ('done','Done')], required=True, default="draft", string="State", track_visibility='onchange')

    sale_truck_status_ids = fields.Many2many('sale.truck.item.status',compute='_compute_sale_truck_status_ids', string="Statuses", track_visibility='onchange')
    sale_truck_status_id = fields.Many2one('sale.truck.item.status', string='Source',required=False, track_visibility='onchange')
    source_qty = fields.Float(related="sale_truck_status_id.qty",string="Source Qty",store=True, track_visibility='onchange')
    source_picking_id = fields.Many2one('stock.picking', related="sale_truck_status_id.picking_id", string="Source Do", required=False,store=True, track_visibility='onchange')

    return_picking_id = fields.Many2one('stock.picking', string="Return Picking", track_visibility='onchange')
    plant_id = fields.Many2one('res.company', string='Plant', track_visibility='onchange')
    location_id = fields.Many2one('stock.location', string='Location', track_visibility='onchange')
    product_id = fields.Many2one('product.product',related='sale_truck_status_id.product_id' ,string='Product', track_visibility='onchange')

    journal_id = fields.Many2one('account.journal', string='Journal', track_visibility='onchange')
    amount = fields.Monetary(string='Amount', track_visibility='onchange')
    move_id = fields.Many2one('account.move', string='Account', track_visibility='onchange')
    debit_account_id = fields.Many2one('account.account', string='Debit Account', track_visibility='onchange')
    credit_account_id = fields.Many2one('account.account', string='Credit Account', track_visibility='onchange')
    currency_id = fields.Many2one('res.currency', string='Currency',default=lambda self: self.env.user.company_id.currency_id.id, track_visibility='onchange')
    debit_amount = fields.Monetary(string='Debit')
    credit_amount = fields.Monetary(string='Credit')
    balance = fields.Monetary(string='Balance',compute='_compute_amount')

    @api.depends('amount')
    def _compute_amount(self):
        for rec in self:
            rec.balance = rec.amount

    @api.onchange('amount')
    def _onchange_amount(self):
        if self.amount > 0:
            self.debit_amount = self.amount
            self.credit_amount = 0.0
        else:
            self.debit_amount = 0.0
            self.credit_amount = abs(self.amount)

    def _fetch_next_seq(self,adjustment_type):
        if adjustment_type == 'deposit':
            sequence = self.env.ref('sales_truck_item_adjustment.sequence_sales_truck_item_adjustment_deposito_galon')
            return sequence.next_by_id()
        else:
            sequence = self.env.ref('sales_truck_item_adjustment.sequence_sales_truck_item_adjustment')
            return sequence.next_by_id()

    @api.model
    def create(self, vals):
        if vals.get('name')=='/':
            vals.update({'name':self._fetch_next_seq(vals.get('adjustment_type'))})
        return super().create(vals)

    def _compute_sale_truck_status_ids(self):
        for rec in self:
            self.sale_truck_status_ids = False

    @api.depends('qty')
    def _compute_qty(self):
        for rec in self:
            rec.qty_after = 0.0
            if rec.qty > 0 and rec.source_qty:
                rec.qty_after = rec.source_qty - rec.qty

    @api.onchange('source_picking_id')
    def _onchange_source_picking_id(self):
        self.sudo().find_default_location()

    def find_default_location(self):
        if self.source_picking_id:
            self.plant_id = self.source_picking_id.sale_id.sale_truck_id.plant_id.id
            self.location_id = self.source_picking_id.sale_id.sale_truck_id.warehouse_id.lot_stock_id.id

    @api.constrains('sale_truck_status_id')
    def _constrains_sale_truck_status_id(self):
        for rec in self:
            if rec.adjustment_type != 'deposit' and not rec.sale_truck_status_id:
                raise UserError(_("Please fill Source Sale Truck."))

    @api.constrains('qty')
    def _constrains_qty(self):
        for rec in self:
            if rec.adjustment_type != 'deposit':
                if rec.qty < 1:
                    raise UserError(_("Please fill adjustment quantity for this document."))
                if rec.qty > rec.source_qty:
                    raise UserError(_("Adjustment qty cannot greater than Source qty."))

    @api.constrains('adjustment_type','product_id','plant_id','location_id')
    def _constrains_adjusment_type(self):
        for rec in self:
            if rec.adjustment_type != 'returned' and rec.product_id and rec.plant_id and rec.location_id:
                raise UserError(_("Cannot change adjustment type for returned document."))
            if rec.adjustment_type != 'deposit' and rec.move_id and rec.amount > 0 and rec.journal_id and rec.debit_account_id and rec.credit_account_id:
                raise UserError(_("Cannot change adjustment type for deposit document."))

    def splitting_current_status(self):
        if self.qty_after>0.0:
            # reduce/update current qty as a computed in qyt_after
            self.sale_truck_status_id.write({'qty':self.qty_after})
        elif self.qty_after==0.0:
            self.sale_truck_status_id.sudo().write({'active':False})
        else:
            raise UserError(_("Qty After can't less than 0.0.\n\nNot a valid Qty!"))

    def post_new_status(self):
        self.sale_truck_status_id.copy({'qty':self.qty,'order_type':self.adjustment_type,'active':True})

    def adjusting_status(self):
        self.ensure_one()
        self.splitting_current_status()
        if self.adjustment_type != 'deposit':
            self.post_new_status()

    @api.onchange('adjustment_type_temp')
    def _onchange_adjustment_type_temp(self):
        if not self.is_deposit:
            self.adjustment_type = self.adjustment_type_temp



    def btn_done(self):
        self.ensure_one()

        self.adjusting_status()

        if self.adjustment_type in ['deposit']:
            self.create_entries()
        elif self.adjustment_type in ['returned']:
            self.done_return()


        self.write({'state':'done'})

    def done_return(self):
        customer_location_id = self.env['stock.location'].search([('usage','=','customer'),('company_id', '=', False)])
        domain = [('code', '=', 'incoming'), ('company_id', '=', self.plant_id.id)]
        picking_type = self.env['stock.picking.type'].with_user(self.plant_id.intercompany_user_id.id).search(domain, limit=1)
        orderlines = []
        orderlines.append((0, 0, {
                    'product_id': self.product_id.id,
                    'product_uom_qty': self.qty_after,
                    'reserved_availability': 0,
                    'quantity_done': self.qty_after,
                    'product_uom': self.product_id.uom_id.id,
                    'company_id': self.plant_id.id,
                    'date': datetime.now().date(),
                    'date_expected': datetime.now().date(),
                    'location_dest_id': self.plant_id.warehouse_id.lot_stock_id.id,
                    'location_id':customer_location_id.id,
                    'name': self.name,
                    'partner_id': self.sale_truck_status_id.partner_id.id,
                    'procure_method': 'make_to_stock',}))

        vals = {'picking_type_id': picking_type.sudo().id,
                'location_dest_id': self.plant_id.warehouse_id.lot_stock_id.id,
                'location_id':customer_location_id.id,
                'scheduled_date': datetime.now(),
                'plant_id': self.plant_id.id,
                'company_id':self.plant_id.id,
                'origin': self.name,
                'partner_id': self.sale_truck_status_id.partner_id.id,
                'move_ids_without_package': orderlines}

        picking_id = self.create_picking(vals)


    def create_picking(self,vals):
        picking_id = self.env['stock.picking'].with_user(self.env.user.company_id.intercompany_user_id.id).create(vals)
        picking_id.action_confirm()
        picking_id.action_assign()
        # check tracking by lot
        for track_lot in picking_id.move_line_ids_without_package:
            if track_lot.product_id.tracking == 'lot':
                lot = self.env['stock.production.lot']
                domain = [('product_id', '=', track_lot.product_id.id),
                              ('company_id', '=', self.sudo().company_id.id)]
                dt_lot = lot.search(domain, limit=1)
                if dt_lot:
                    track_lot.lot_id = dt_lot.id
                else:
                    # crete lot
                    val = {'product_id': track_lot.product_id.id,
                           'company_id': self.sudo().company_id.id,
                           'name': track_lot.name}
                    dt_lot = lot.create(val)
                    track_lot.lot_id = dt_lot.id
        validating = picking_id.button_validate()
        if type(validating)==dict:
            res_model = validating.get('res_model')
            if res_model == 'stock.immediate.transfer':
                res_id = validating.get('res_id')
                Wizard = self.env['stock.immediate.transfer'].browse(res_id)
                Wizard.process() # process if wizard showed
            else:
                raise ValidationError(_("Error in validating Delivery Order. Ref: {%s}")%(validating['res_model']))
        return picking_id

    def create_entries(self):
        move_id = self.env['account.move'].create({
            'type': 'entry',
            'ref': 'Entries Of %s' % (self.name,),
            'journal_id':self.journal_id.id,
            'date': datetime.now().date(),
            'line_ids': [(0, 0, {
                'name': 'Amount',
                'account_id': self.debit_account_id.id,
                'partner_id':self.partner_id.id,
                'debit': abs(self.amount),
                'credit': 0.0,
            }),(0, 0, {
                'name': 'Amount',
                'account_id': self.credit_account_id.id,
                'partner_id':self.partner_id.id,
                'debit': 0.0,
                'credit': abs(self.amount),
            })]
        })
        if move_id:
            self.move_id = move_id
            self.move_id.action_post()