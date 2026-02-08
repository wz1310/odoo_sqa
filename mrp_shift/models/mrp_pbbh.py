""" Permintaan Bahan Baku Harian """
from odoo import models, fields, _ , api
from odoo.tools.float_utils import float_compare
from datetime import datetime, date
from odoo.exceptions import UserError, ValidationError


class Mrppbbh(models.Model):
    """ Define Permintaan Bahan Baku Harian """

    _name = 'mrp.pbbh'
    _description = 'Mrp Permintaan Bahan Baku Harian'
    _inherit = ["approval.matrix.mixin",'mail.thread', 'mail.activity.mixin']

    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 readonly=True, index=True, default=lambda self: self.env.company)

    location_id = fields.Many2one('stock.location','Location',domain=[('usage','=','production')])
    mrp_pbbh_line_ids = fields.One2many('mrp.pbbh.line', 'mrp_pbbh_id', store=True)
    name = fields.Char(default='/', copy=False, track_visibility='onchange')
    product_id = fields.Many2one('product.product', string="SKU",
                                 required=True, track_visibility='onchange')
    product_tmpl_id = fields.Many2one('product.template')
    rph_id = fields.Many2one('mrp.rph', string="RPH", required=True,
                             track_visibility='onchange')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('done', 'Done'),
        ('cancel', 'Canceled')
    ], string='State',default='draft',required=True, track_visibility='onchange')
    total_qty = fields.Float(compute='_compute_total_qty',store=True, track_visibility='onchange')
    bom_id = fields.Many2one('mrp.bom', 'Bill of Material', required=True,
                             track_visibility='onchange')
    date = fields.Date(default=date.today(), track_visibility='onchange')
    picking_count = fields.Integer(compute='_compute_picking', string='Picking count', default=0, store=True)
    picking_ids = fields.One2many('stock.picking', 'mrp_pbbh_id', string='Internal Transfer', copy=False, store=True)
    
    rpm_count = fields.Integer(compute='_compute_rpm', string='RPM count', default=0, store=True)
    #rpm_ids = fields.One2many('mrp.rpm', 'pbbh_id', string='RPM', copy=False, store=True)
    location_raw_material = fields.Selection([('1','Location Raw 1'), ('2','Location Raw 2')], string="Location Raw Material", required=True, default="1")
    dest_location_raw_material = fields.Many2one('stock.location', string="Destination Raw Material", check_company=True, required=True, domain=[('production_for_pbbh','=', True)])

    @api.onchange('rph_id')
    def onchange_product_id(self):
        if self.rph_id:
            self.product_id = self.rph_id.product_id
            self.product_tmpl_id = self.rph_id.product_tmpl_id
            self.bom_id = self.rph_id.bom_id

    @api.depends('picking_ids', 'picking_ids.mrp_pbbh_id')
    def _compute_picking(self):
        for record in self:
            record.picking_count = len(record.picking_ids)

    # @api.depends('rpm_ids', 'rpm_ids.pbbh_id')
    # def _compute_rpm(self):
    #     for record in self:
    #         record.rpm_count = len(record.rpm_ids)

    @api.onchange('bom_id', 'total_qty')
    def onchange_bom_id(self):
        if self.bom_id:
            new_lines = self.env['mrp.pbbh.line']
            for data in self.bom_id.bom_line_ids:
                vals = {'product_id': data.product_id.id,
                        'qty' : (data.product_qty / self.bom_id.product_qty) * self.total_qty,
                        'product_uom_id': data.product_uom_id.id
                        }
                new_lines += new_lines.new(vals)
            self.mrp_pbbh_line_ids = new_lines

    @api.model
    def create(self, values):
        res = super(Mrppbbh, self).create(values)
        sequence = self.env.ref('mrp_shift.sequence_mrp_pbbh')
        
        if sequence:
            name = self.env['ir.sequence'].next_by_code(sequence.code)
            res.name = name
        return res
    
    def action_view_transfer(self):
        self.ensure_one()
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        pickings = self.mapped('picking_ids')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = pickings.id
        action['context'] = dict(self._context, default_origin=self.name, create=False)
        return action

    # def action_view_rpm(self):
    #     self.ensure_one()
    #     action = self.env.ref('mrp_shift.mrp_rpm_action').read()[0]
    #     rpm_ids = self.mapped('rpm_ids')
    #     if len(rpm_ids) > 1:
    #         action['domain'] = [('id', 'in', rpm_ids.ids)]
    #     elif rpm_ids:
    #         form_view = [(self.env.ref('mrp_shift.mrp_rpm_view_form').id, 'form')]
    #         if 'views' in action:
    #             action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
    #         else:
    #             action['views'] = form_view
    #         action['res_id'] = rpm_ids.id
    #     return action
    
    def button_confirm(self):
        self.checking_approval_matrix(add_approver_as_follower=True, data={'state':'waiting_approval'})
        return self.write({
            'state':'waiting_approval'
        })

    def button_approve(self):
        self.approving_matrix(post_action='action_approve')

    def action_approve(self):
        operation_type = self.env['stock.picking.type'].search([
            ('code','=','internal'), ('company_id', '=', self.company_id.id)
        ], limit=1)
        warehouse_id = self.env['stock.warehouse'].search([
            ('company_id', '=', self.company_id.id),
        ], limit=1)
        transit_location_id = self.env['stock.location'].search([
            ('company_id', '=', self.company_id.id),
            ('usage', '=', 'transit'),
            ('check_for_transit_bahan_baku', '=', True)
        ], limit=1)
        production_location_id = self.dest_location_raw_material
        # self.env['stock.location'].search([
        #     ('company_id', '=', self.company_id.id),
        #     # ('usage', '=', 'production')
        #     ('production_for_pbbh','=',True)
        # ], limit=1)
        group_id = self.env['procurement.group'].create({
                'name': self.name,
            })
        if warehouse_id:
            if not warehouse_id.location_raw_material_id:
                raise ValidationError('Please set location raw material in warehouse %s' % (warehouse_id.name))
            if not warehouse_id.location_raw_material_id_2:
                raise ValidationError('Please set location raw material 2 in warehouse %s' % (warehouse_id.name))
            if not warehouse_id.production_type_id:
                raise ValidationError('Please set Production Operation type in warehouse %s' % (warehouse_id.name))
            if not warehouse_id.raw_material_type_id:
                raise ValidationError('Please set Raw Material Operation type in warehouse %s' % (warehouse_id.name))
        if not transit_location_id:
            raise ValidationError('Please check transit location in your company')
        else:

            raw_location = warehouse_id.location_raw_material_id
            if self.location_raw_material == "2":
                raw_location = warehouse_id.location_raw_material_id_2

            pick1 = self.create_picking(raw_location, transit_location_id,
                                        warehouse_id.raw_material_type_id, group_id)
            pick2 = self.with_context(origin=pick1).create_picking(transit_location_id, production_location_id,
                                        warehouse_id.production_type_id, group_id)
            pickings = pick1+pick2
            pickings.action_confirm()
        self.state = 'approved'

    def create_picking(self, src_loc, dst_loc, pick_type, group):
        StockPicking = self.env['stock.picking']
        picking = self.env['stock.picking']
        for order in self:
            vals = {
                'picking_type_id': pick_type.id,
                'user_id': False,
                'date': fields.Date.today(),
                'origin': self.name,
                'location_dest_id': dst_loc.id,
                'location_id': src_loc.id,
                'company_id': self.company_id.id,
                'group_id': group.id if group else False,
                'mrp_pbbh_id': self.id
            }
            picking = StockPicking.create(vals)
            picking.group_id = group
            moves = order.mrp_pbbh_line_ids._create_stock_moves(picking)
            old_picking = self.env.context.get('origin')
            for data in moves:
                # move_id = self.env['stock.move']
                if old_picking:
                    move_id = self.env['stock.move'].search([('picking_id', '=', old_picking.id),
                                                             ('product_id', '=', data.product_id.id)],limit=1)
                    if move_id:
                        data.move_orig_ids = [(4, move_id.id)]
        return picking

    def button_reject(self):
        self.rejecting_matrix()
        self.state = 'rejected'

    def open_reject_message_wizard(self):
        self.ensure_one()
        form = self.env.ref('approval_matrix.message_post_wizard_form_view')
        context = dict(self.env.context or {})
        context.update({'default_prefix_message':"<h4>Rejecting Pembelian Bahan Baku Harian</h4>","default_suffix_action": "button_reject"}) #uncomment if need append context
        context.update({'active_id':self.id,'active_ids':self.ids,'active_model':'mrp.pbbh'})
        res = {
            'name': "%s - %s" % (_('Rejecting Pembelian Bahan Baku Harian'), self.name),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'message.post.wizard',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res

    def button_done(self):
        for data in self:
            if all(picking.state == 'done' for picking in data.picking_ids.filtered(lambda x:x.state != 'cancel')):
                return self.write({
                    'state' : 'done'
                })
            else:
                raise ValidationError('Please Validate transfer picking')

    @api.depends('rph_id', 'rph_id.mrp_rph_line_ids', 'rph_id.mrp_rph_line_ids.qty', 'date')
    def _compute_total_qty(self):
        for data in self:
            if data.date:
                rph_line_id = data.rph_id.mrp_rph_line_ids.filtered(lambda x:x.date == data.date)
                data.total_qty = rph_line_id.qty

    # @api.onchange('product_id', 'date', 'total_qty')
    # def _onchange_field_product(self):
    #     if self.product_id:
    #         for rec in self:
    #             bom_ids = rec.env['mrp.bom'].search([
    #                 ('product_tmpl_id.id', '=', rec.product_id.id)
    #             ])
    #             pbbh_line = []
    #             for line in bom_ids.bom_line_ids:
    #                 vals = (0, 0, {'product_id' : line.product_id.id,
    #                                 'qty': line.product_qty * self.total_qty})
    #                 pbbh_line.append(vals)
    #             rec.update({'mrp_pbbh_line_ids': pbbh_line})
    
    # def action_view_rpm(self):
    #     action = self.env.ref('mrp_shift.mrp_rpm_action')
    #     result = action.read()[0]
    #     res = self.env.ref('mrp_shift.mrp_rpm_view_form', False)
    #     form_view = [(res and res.id or False, 'form')]
    #     if 'views' in result:
    #         result['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
    #     else:
    #         result['views'] = form_view
    #     return result

    def wizard_create_rpm(self):
        self.ensure_one()
        context = dict(self.env.context or {})
        context['default_pbbh_id'] = self.id
        form = self.env.ref('mrp_shift.view_create_rpm_wizard_form')
        res = {
            'name': "Create RPM",
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'create.rpm',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res

    def button_cancel(self):
        for data in self:
            if all(picking.state not in ('cancel', 'done') for picking in data.picking_ids):
                data.picking_ids.action_cancel()
                return self.write({
                    'state':'cancel'
                })
            else:
                raise ValidationError('You cannot cancel pbbh that already have picking state is done')

    def button_set_draft(self):
        return self.write({
            'state':'draft'
        })
            
class MrppbbhLine(models.Model):
    """ Define Permintaan Bahan Baku Harian Line """

    _name = 'mrp.pbbh.line'
    _description = 'Mrp pbbh line'

    product_id = fields.Many2one('product.product',string="Material")
    mrp_pbbh_id = fields.Many2one('mrp.pbbh',ondelete='cascade',index=True)
    qty = fields.Float()
    qty_available = fields.Float('Qty Available',compute="_compute_qty_available")
    product_uom_id = fields.Many2one('uom.uom')
    qty_to_transfer = fields.Float('Qty to Transfer')


    #dion#
    def _compute_qty_available(self):
        for rec in self:
            if rec.mrp_pbbh_id.location_id:
                qty = self.env['stock.quant'].search([('product_id', '=', rec.product_id.id), ('location_id', '=', rec.mrp_pbbh_id.location_id.id)])
                if qty:
                    for each in qty:
                        if rec.qty_available:
                            rec.qty_available += each.quantity
                        else:
                            rec.qty_available = 0
                else:
                    rec.qty_available = 0
            else:
                rec.qty_available = 0

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id

    def _prepare_stock_moves(self, picking):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        warehouse_id = self.env['stock.warehouse'].search([
            ('company_id', '=', self.mrp_pbbh_id.company_id.id),
        ], limit=1)
        template = {
            # truncate to 2000 to avoid triggering index limit error
            # TODO: remove index in master?
            'name': (self.mrp_pbbh_id.name or '')[:2000],
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'date': fields.Date.today(),
            'date_expected': fields.Date.today(),
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
            'picking_id': picking.id,
            'state': 'draft',
            'company_id': picking.company_id.id,
            # 'price_unit': price_unit,
            'picking_type_id': picking.picking_type_id.id,
            'group_id': picking.group_id.id,
            'origin': picking.name,
            'product_uom_qty': self.qty_to_transfer,
            'propagate_date': False,
            'propagate_date_minimum_delta': 0,
            'propagate_cancel': False,
            # 'route_ids': self.order_id.picking_type_id.warehouse_id and [(6, 0, [x.id for x in self.order_id.picking_type_id.warehouse_id.route_ids])] or [],
            'warehouse_id': warehouse_id.id,
        }
        res.append(template)
        return res

    def _create_stock_moves(self, picking):
        values = []
        for line in self:
            for val in line._prepare_stock_moves(picking):
                values.append(val)
        return self.env['stock.move'].create(values)