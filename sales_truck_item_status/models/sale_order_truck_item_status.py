from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
import logging
_logger = logging.getLogger(__name__)

class SaleTruckItemStatus(models.Model):
    _name = 'sale.truck.item.status'
    _description = 'Sale Truck Item Status'
    _order = "id desc"

    order_type = fields.Selection([
        ('borrow', 'Pinjam'),
        # ('borrow-in', 'Incoming Borrow'),
        ('change', 'EX-Change/Tukar'),
        ('deposit', 'Deposit'),
        ('returned', 'Returned/Kembali'),
        ('to_bill', 'To Bill/Invoice')
    ], string='Order Type',required=True, track_visibility='onchange')
    picking_id = fields.Many2one('stock.picking', string='Source Document', track_visibility='onchange')
    product_id = fields.Many2one('product.product', string='Product')
    qty = fields.Float(string='Qty', track_visibility='onchange')
    origin = fields.Char(string='Origin',required=True, track_visibility='onchange')
    transaction_date = fields.Datetime(string='Transaction Date', track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', string='Customer',required=True, track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company',required=True, track_visibility='onchange')
    active = fields.Boolean(string="Active", default=True)

    move_type = fields.Selection([('outgoing','Outgoing'),('incoming','Incoming')], string="Move Type", compute="_compute_move_type", inverse="_inverse_qty", store=True)
    qty_calc = fields.Float(string="Qty(Calc)", compute="_compute_move_type", inverse="_inverse_qty", store=True)

    sale_truck_id = fields.Many2one('sale.order.truck', required=False, string="Sale Order Truck", compute="_compute_sale_truck_id", store=True, inverse="_inverse_sale_truck")



    # @return env sale.order.truck
    def _find_sot_partner_by_picking(self):
        self.ensure_one()
        picking = self.sudo().picking_id

        SOT = self.env['sale.order.truck']
        # transit_out_picking_id
        # return_material_picking
        res =  SOT.search([('return_material_picking','=',picking.sudo().ids)])

        so = self.env['sale.order'].search([('sale_truck_id','=',picking.sudo().ids), ('partner_id','=',self.partner_id.sudo().id)])
        if len(so):
            res += so.mapped('sale_truck_id')

        return res

    @api.depends('picking_id')
    def _compute_sale_truck_id(self):
        for rec in self:
            res = rec.sale_truck_id.id
            if rec.id and rec.sudo().picking_id.sale_truck_id.id:
                res = rec.sudo().picking_id.sale_truck_id.id

            if not res:
                sot = rec._find_sot_partner_by_picking()
                if len(sot):
                    res = sot[0].id
            
            rec.sale_truck_id = res

    def _inverse_sale_truck(self):
        return True

    @api.onchange('sale_truck_id')
    def _onchange_sale_truck_id(self):
        domain = {'picking_id':['|',('state','=','done'), ('sale_truck_id','!=',False)]}
        res = {'domain':domain}
        if self.sale_truck_id.id:
            # domain_picking = domain.get('picking_id')
            domain_picking = [('id','in',self.sale_truck_id.return_material_picking.ids + self.sale_truck_id.sale_ids.mapped('picking_ids').ids)]
            res['domain'].update({'picking_id':domain_picking})
        return res


    def _inverse_qty(self):
        for rec in self:
            if rec.move_type=='incoming':
                rec.qty_calc = 0.0 - float(abs(rec.qty))

    def open_form(self):
        self.ensure_one()
        form = self.env.ref('sales_truck_item_status.sales_truck_item_status_form_view')
        context = dict(self.env.context or {})
        # context.update({}) #uncomment if need append context
        res = {
            'name': "%s - %s" % (_('Stock Card - Update'), self.partner_id.display_name),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.truck.item.status',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new',
            'res_id': self.id
        }
        return res

    @api.depends('order_type')
    def _compute_move_type(self):
        for rec in self:
            res_type = 'outgoing'
            res_qty = rec.qty
            if rec.order_type in ['borrow-in','returned','change']:
                res_type = 'incoming'
                res_qty = 0.0 - float(abs(rec.qty))
            
            rec.update({
                'move_type':res_type,
                'qty_calc':res_qty
            })
    
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, rec.partner_id.name+' - '+rec.order_type))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        else:
            domain = ['|', ('partner_id.name', operator, name), ('picking_id.name', operator, name)]
        rec = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return models.lazy_name_get(self.browse(rec).with_user(name_get_uid))
    
    @api.model
    def fetch_borrow(self, partner_id):
        picking_id = self.env['stock.picking'].search([('partner_id','=',partner_id),('is_fetch_borrow','=',False), ('sale_truck_id','!=',False), ('state','=','done')])
        for picking in picking_id:
            for move in picking.move_ids_without_package.filtered(lambda r: r.product_id.reg_in_customer_stock_card ==  True):
                if move.product_id.sale_truck == True:
                    qty = move.quantity_done
                    if move.product_id.qty_field and move.product_id.qty_field == 'difference_qty':
                        material_id = self.env['sale.order.truck.material'].search([('sale_truck_id','=',move.sale_truck_id.id),('product_id','=',move.product_id.id),('partner_id','=',move.partner_id.id),('state','=','done')])
                        qty = material_id.different_qty

                    vals = {
                        'order_type': 'borrow',
                        'picking_id' :picking.id,
                        'origin' :picking.name,
                        'partner_id' : picking.partner_id.id,
                        'company_id' : picking.company_id.id,
                        'transaction_date' : picking.date_done,
                        'product_id' : move.product_id.id,
                        'qty' : qty
                    }

                    sale_truck_status_id = self.env['sale.truck.item.status'].create(vals)
                    move.sale_truck_status_id = sale_truck_status_id
            picking.is_fetch_borrow = True

    @api.model
    def fetch_change(self):
        pass
    
    @api.model
    def fetch_deposit(self):
        pass

class SaleTruckDispenserStatus(models.Model):
    _name = 'sale.truck.dispenser.status'
    _description = 'Sale Truck Dispenser Status'
    _order = "id desc"

    brand = fields.Text(string='Brand', track_visibility='onchange')
    new_brand = fields.Text(string=' New Brand', track_visibility='onchange')
    buy_date = fields.Date(string='Buy Date', track_visibility='onchange')
    serial_number = fields.Char(string='Serial Number', track_visibility='onchange')
    new_serial_number = fields.Char(string='New Serial Number', track_visibility='onchange')
    qty = fields.Integer(string='Qty', track_visibility='onchange', default="1")
    deliver_date = fields.Date(string='Date Deliver To Customer', track_visibility='onchange')
    #condition = fields.Text(string='Condition', track_visibility='onchange')
    condition = fields.Selection([('good','Good'),('broken','Broken')],'Condition')
    #type_of_lease = fields.Text(string='Type of Lease', track_visibility='onchange')
    type_of_lease = fields.Selection([('borrow','Borrow'),('rent','Rent'),
                                      ('return','Return'),
                                      ('change','Change')],'Type of Lease')
    return_date = fields.Date('Return Date')
    picking_id = fields.Many2one('stock.picking', string='Source Document', track_visibility='onchange')
    partner_id = fields.Many2one('res.partner',string='Customer', track_visibility='onchange')
    partner_name = fields.Char(related='partner_id.name',string='Customer Name')
    partner_code = fields.Char(related='partner_id.code',string='Customer Code')
    company_id = fields.Many2one('res.company',string='Company',required=True, track_visibility='onchange',default=lambda self: self.env.company)
    rental_price_to_vendor = fields.Float('Rental Price to Vendor',required=True, track_visibility='onchange')
    rental_price_to_customer = fields.Float('Rental Price to Customer',required=True, track_visibility='onchange')
    vendor_ids = fields.Many2many('res.partner',string='Vendor', domain=[('supplier','=',True)])
    
    def name_get(self):
        result = []
        for rec in self:
            brand = rec.brand or ''
            serial = rec.serial_number or ''
            result.append((rec.id, brand+' - '+serial))
        return result

    @api.model
    def fetch_borrow(self):
        picking_id = self.env['stock.picking'].search([('is_fetch_dispenser','=',False), ('sale_truck_id','!=',False), ('state','=','done')])
        for picking in picking_id:
            for move in picking.move_ids_without_package:
                if move.product_id.sale_truck_dispenser == True:
                    vals = {
                        'brand': '',
                        'buy_date' :picking.date_done,
                        'serial_number' : move.dispenser_lot_id.display_name,
                        'qty' : move.quantity_done,
                        'deliver_date' : picking.date_done,
                        'condition' : '',
                        'type_of_lease' : '',
                        'picking_id' :picking.id,
                        'partner_id' : picking.partner_id.id,
                        'company_id' : picking.company_id.id
                    }
        
                    sale_truck_dispenser_id = self.env['sale.truck.dispenser.status'].create(vals)
                    move.sale_truck_dispenser_id = sale_truck_dispenser_id
            picking.is_fetch_dispenser = True

    @api.model
    def fetch_change(self):
        pass
    
    @api.model
    def fetch_deposit(self):
        pass
