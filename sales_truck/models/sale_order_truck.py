"""File sale order truck"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import math

import logging
_logger = logging.getLogger(__name__)

class SaleOrderTruck(models.Model):
	_name = "sale.order.truck"
	_inherit = ["approval.matrix.mixin",'mail.thread', 'mail.activity.mixin']
	_description = "Sale Order Truck"
	_order = "id desc"
	def read(self, fields=None, load='_classic_read'):
		return super(SaleOrderTruck, self.sudo()).read(fields=fields, load=load)

	name = fields.Char(string="Name", track_visibility='onchange')
	team_id = fields.Many2one('crm.team', string="Team", track_visibility='onchange')
	# sales_id = fields.Many2one('res.users', string="Sales", required=True, track_visibility='onchange')
	start_date = fields.Date(default=fields.Date.today(), string="Start Date", track_visibility='onchange')
	end_date = fields.Date(default=fields.Date.today(), string="End Date", track_visibility='onchange')
	company_id = fields.Many2one('res.company', default=lambda self: self.env.company.id,\
								 string="Company", track_visibility='onchange')
	state = fields.Selection([('draft', 'Draft'), ('waiting_approval', 'Waiting Approval'), ('submited', 'Approved'), 
							  ('confirmed', 'Confirmed'), ('refuse', 'Refuse'),
							  ('done', 'Done'), ('rejected','Rejected'), ('cancel','Cancelled')], string='Status', default='draft', track_visibility='onchange')
	plant_id = fields.Many2one('res.company', string="Plant", required=True, check_company=False, context={'all_companies':True}, track_visibility='onchange')
	
	warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse Location", required=True, ondelete="restrict", onupdate="restrict", context={'all_companies':True}, track_visibility='onchange')
	
	vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle", track_visibility='onchange')    
	order_line_ids = fields.One2many('sale.order.truck.line', 'sale_truck_id', string="Orderline", track_visibility='onchange', copy=True)
	sale_truck_material_ids = fields.One2many('sale.order.truck.material', 'sale_truck_id', string="Material",copy=False, track_visibility='onchange')
	return_sale_truck_material_ids = fields.Many2many('sale.order.truck.material', string="Material (non return)", compute="_compute_material_ids")
	non_return_sale_truck_material_ids = fields.Many2many('sale.order.truck.material', string="Material (non return)", compute="_compute_material_ids")
	
	partner_ids = fields.Many2many('res.partner',compute='_compute_partner_ids',string='Partner',store=True, track_visibility='onchange')
	truck_dispanser_ids = fields.One2many('sale.order.truck.dispanser', 'sale_truck_id', string="Dispanser", track_visibility='onchange')


	load_truck_picking_id = fields.Many2one('stock.picking', "Load to Truck", ondelete="cascade", onupdate="cascade")
	transit_out_picking_id = fields.Many2one('stock.picking', "Transit Picking Out", ondelete="cascade", onupdate="cascade")
	transit_in_picking_id = fields.Many2one('stock.picking', "Transit Picking IN", ondelete="cascade", onupdate="cascade")
	company_in_picking_id = fields.Many2one('stock.picking', "Receiving", ondelete="cascade", onupdate="cascade")
	return_material_picking = fields.Many2one('stock.picking', "Return", ondelete="cascade", onupdate="cascade")

	rejecting_picking_id = fields.Many2one('stock.picking', "Rejecting Picking", ondelete="cascade", onupdate="cascade")

	sale_ids = fields.One2many('sale.order', 'sale_truck_id', string="Sales Order")
	sale_count = fields.Integer(compute="_compute_sale_count", string="Sale Count")

	vehicle_model_id = fields.Many2one('fleet.vehicle.model', string='Vehicle Model', track_visibility='onchange')
	vehicle_driver_id = fields.Many2one('res.partner', string='Vehicle Driver', track_visibility='onchange', domain=[('customer','=',False),('supplier','=',False)])

	currency_id = fields.Many2one('res.currency', string='Currency',track_visibility='onchange',default=lambda self: self.env.company.currency_id.id)
	amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all',track_visibility='onchange')
	amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all',track_visibility='onchange')
	amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all',track_visibility='onchange')
	order_pickup_method_id = fields.Many2one('order.pickup.method', string="Pickup Method", required=False, ondelete="restrict", onupdate="restrict", track_visibility="onchange")

	plant_sale_id = fields.Many2one('sale.order', string="Plant Sale Order", ondelete="cascade", onupdate="cascade")
	purchase_id = fields.Many2one('purchase.order', string="Purchase Order", ondelete="cascade", onupdate="cascade")

	receive_material = fields.Boolean('Receiving', default=False, help="Check if only receiving material")

	status_so = fields.Selection([('normal','Normal'),
								  ('overdue','Overdue'),
								  ('overlimit','Overlimit'),
								  ('overdue_overlimit','Overdue & Overlimit')],compute="_set_status_so", store=True)



	@api.depends('order_line_ids')
	def _set_status_so(self):
		for rec in self:
			if any(line.is_overdue == True for line in rec.order_line_ids):
				rec.status_so = 'overdue'
			elif any(line.is_overlimit == True for line in rec.order_line_ids):
				rec.status_so = 'overlimit'
			elif any(line.is_overlimit == True and line.is_overdue == True for line in rec.order_line_ids):
				rec.status_so = 'overdue_overlimit'
			else:
				rec.status_so = 'normal'


	def _compute_material_ids(self):
		for rec in self:
			rec.update({
				'non_return_sale_truck_material_ids': [(6,0,rec.sale_truck_material_ids.filtered(lambda r:r.sale_truck_line_id.id!=False).ids)],
				'return_sale_truck_material_ids': [(6,0,rec.sale_truck_material_ids.filtered(lambda r:r.return_qty>0.0).ids)],
				})
	
	@api.depends('order_line_ids.price_total')
	def _amount_all(self):
		"""
		Compute the total amounts of the SO.
		"""
		for order in self:
			amount_untaxed = amount_tax = 0.0
			for line in order.order_line_ids:
				amount_untaxed += line.price_subtotal
				amount_tax += line.price_tax
			order.update({
				'amount_untaxed': amount_untaxed,
				'amount_tax': amount_tax,
				'amount_total': amount_untaxed + amount_tax,
			})

	@api.onchange('vehicle_id')
	def onchange_vehicle_id(self):
		driver_id = False
		if self.vehicle_id.id:
			driver_id = self.vehicle_id.driver_id.id
			
		self.vehicle_driver_id = driver_id

	def open_sale_ids(self):
		action = self.env['ir.actions.act_window'].for_xml_id('sale', 'action_quotations_with_onboarding')
		action.update({'context':"{}"})
		action.update({'domain':[('id','in',self.sudo().sale_ids.ids)]})
		return action

	@api.depends('sale_ids')
	def _compute_sale_count(self):
		for rec in self:
			rec.sale_count = len(rec.sudo().sale_ids)

	@api.constrains('team_id')
	def _constrains_team(self):
		for rec in self:
			for line in self.order_line_ids:
				line.partner_id.check_partner_pricelist(rec.team_id)

	@api.constrains('truck_dispanser_ids')
	def _constrains_truck_dispanser_ids(self):
		for rec in self:
			serial_lot = []
			for line in rec.truck_dispanser_ids:
				if line.product_id.tracking == 'serial':
					if line.lot_id.id in serial_lot:
						raise UserError(_("Cannot select same lot for serializable product"))
					else:
						serial_lot.append(line.lot_id.id)

	def unlink(self):
		if any(truck.state not in ['draft'] for truck in self) and self.user_has_groups('!base.group_system'):
			raise UserError(_('Cannot delete non draft a Sales order Truck.'))
		return super(SaleOrderTruck,self).unlink()

	def _compute_partner_ids(self):
		for this in self:
			this.partner_ids = self.env['res.partner'].search([('customer','=',True)]).ids or False

	# @api.onchange('team_id')
	# def _onchange_sales_id(self):
	#     if self.team_id:
	#         return {'domain': {'sales_id': [('id', '=', self.team_id.sales_user_ids.ids)]}}

	@api.onchange('plant_id')
	def _onchange_warehouse_id(self):
		if self.plant_id:
			self.warehouse_id = self.plant_id.warehouse_id.id
			return {'domain': {'warehouse_id': [('company_id', '=', self.with_user(self.env.company.intercompany_user_id.id).plant_id.id)]}}
		else:
			self.warehouse_id = False
			return {'domain': {'warehouse_id': [('id', '=', False)]}}

	@api.model
	def create(self, vals):
		vals['name'] = self.env['ir.sequence'].next_by_code('sale.order.truck')
		return super(SaleOrderTruck, self).create(vals)
	def _submit_truck(self):
		if len(self.order_line_ids) == 0:
			raise  UserError(_('Can not sending product'))
		for rec in self.order_line_ids:
			if len(rec.product_id.sale_truck_material_ids) == 0:
				raise UserError(_("This product %s has not any materials product") % (rec.product_id.display_name))

		self.checking_approval_matrix(add_approver_as_follower=True, data={'state':'waiting_approval'})

	def _submit_receiving(self):
		if not len(self.sale_truck_material_ids.filtered(lambda r:r.receive_material)):
			raise ValidationError(_("Please Input Item(s) to receive!"))
		for line in self.sale_truck_material_ids:
			line.update({'return_qty':line.product_uom_qty})
		self.checking_approval_matrix(add_approver_as_follower=True, data={'state':'waiting_approval'})

	def customer_must_unique(self):
		self.ensure_one()
		partners = self.order_line_ids.mapped('partner_id')
		only1 = partners.mapped(lambda r:len(self.order_line_ids.filtered(lambda rr:rr.partner_id == r))==1)
		if not all(only1):
			raise UserError(_("Double Customer.!Please check!"))
		

	def btn_submit(self):
		
		self.customer_must_unique()
		if self.receive_material:
			self._submit_receiving()
		else:
			self._submit_truck()


	def _check_stock_qty_on_location(self):
		location_id = self.sudo().warehouse_id.lot_stock_id
		self = self.sudo().with_context(location=location_id.id,force_company=self.plant_id.id,allowed_company_ids=self.plant_id.ids)
		for rec in self.order_line_ids:
			qty_available = rec.product_id.qty_available
			if rec.product_uom_qty > qty_available:
				raise UserError(_('Stock quantities for product %s not available on this location!') % (self.product_id.display_name))
		for rec in self.sale_truck_material_ids:
			qty_available = rec.product_id.qty_available
			if rec.product_uom_qty > qty_available:
				raise UserError(_('Stock quantities for product %s not available on this location!') % (self.product_id.display_name))


	def btn_refuse(self):
		self.ensure_one()
		self.update({
			# 'plant_id':False,
			# 'warehouse_id':False,
			'vehicle_id':False,
			'vehicle_driver_id':False,
			'state':'refuse',
		})
	
	def action_approve(self):
		self.state = 'submited'
	
	def btn_reject(self):
		self.ensure_one()
		self.rejecting_matrix()
		self.state = 'rejected'

	def btn_approve(self):
		self.ensure_one()
		if self.state == 'waiting_approval':
			self.approving_matrix(post_action='action_approve')
			if not self.receive_material:
				self._generate_materials()
			else:
				self.btn_confirm()

			self.order_line_ids._update_approve_qty()

	def _vehicle_must_filled(self):
		self.ensure_one()
		if not self.vehicle_id:
			raise UserError(_('Please Select Vehicle!'))

	def _create_move_lines(self, records, move, qty_field):
		self.ensure_one()
		MoveLine = self.env['stock.move.line']

		# move_lines = MoveLine
		move_lines = []
		for rec in records:
			err=True
			try:
				has_lot_ids = getattr(rec, 'lot_ids')
				err=False
			except Exception as e:
				has_lot_ids = False
			
			if not err:
				if not len(has_lot_ids):
					raise UserError(_("Please Select Lot for %s" % (rec.product_id.display_name,)))
				# if not err
				# it has has_lot_ids
				for lot in has_lot_ids.sudo():
					lot = lot.sudo()
					Lot = self.env['stock.production.lot'].sudo().with_context(force_company=move.get('company_id'),allowed_company_ids=[move.get('company_id')]).search([('product_id','=',rec.product_id.id), ('name','=',lot.lot_id.name),('company_id','=',move.get('company_id'))])
					if not len(Lot):
						Lot = self.env['stock.production.lot'].create({
							'name':lot.lot_id.name,
							'company_id':move.get('company_id'),
							'product_id':rec.product_id.id
						})

					qty_done = getattr(lot, qty_field)
					if qty_done:

						new_rec = dict(product_id=rec.product_id.id, 
								picking_id=move.get('picking_id'),
								product_uom_id=rec.product_id.uom_id.id, 
								lot_id=Lot.sudo().id,
								qty_done=qty_done,
								# product_uom_qty=getattr(lot, qty_field),
								location_id=move.get('location_id'), 
								location_dest_id=move.get('location_dest_id'), 
								company_id=move.get('company_id'))
						# move_lines += MoveLine.create(new_rec)
						move_lines.append((0, 0, new_rec))
			else:
				Lot = rec.sudo().lot_id
				find_lot = self.env['stock.production.lot'].sudo().with_context(force_company=move.get('company_id'),allowed_company_ids=[move.get('company_id')]).search([('product_id','=',rec.product_id.id), ('name','=',rec.sudo().lot_id.name),('company_id','=',move.get('company_id'))])
				if not len(find_lot):
					Lot = self.env['stock.production.lot'].create({
						'name':rec.sudo().lot_id.name,
						'company_id':move.get('company_id'),
						'product_id':rec.product_id.id
					})

				new_rec = dict(product_id=rec.product_id.id, 
						picking_id=move.get('picking_id'),
						product_uom_id=rec.product_id.uom_id.id, 
						lot_id=Lot.id,
						qty_done=getattr(rec, qty_field),
						
						location_id=move.get('location_id'), 
						location_dest_id=move.get('location_dest_id'), 
						company_id=move.get('company_id'))
				# move_lines += MoveLine.create(new_rec)
				move_lines.append((0, 0, new_rec))
		return move_lines

	def _create_moves(self, o2m_field, picking, company_id, picking_type, src_location, dest_location, ref=False, qty_field='qty'):
		self.ensure_one()
		Moves = self.env['stock.move']
		
		O2mField = getattr(self, o2m_field)
		Products = O2mField.mapped('product_id')
		new_moves = Moves
		# loop each product
		for product in Products:
			# for each
			# if product == lot or serial
			matched_related = O2mField.filtered(lambda r:r.product_id.id==product.id) # found dipenser with matched product

			quantity = sum(matched_related.mapped(qty_field))
			
			move_rec = {
				'picking_id':picking.sudo().id,
				'product_id': product.id,
				
				# 'dispenser_lot_id': this.lot_id.id,
				# 'quantity_done':quantity,
				'product_uom_qty':quantity,
				'product_uom': product.uom_id.id,
				'company_id': company_id.sudo().id,
				'date': fields.Datetime.today(),
				'date_expected': fields.Datetime.today(),
				'location_dest_id': dest_location.sudo().id,
				'location_id': src_location.sudo().id,
				'name': "%s - %s" % (product.display_name, self.name,),
				'procure_method': 'make_to_stock',
				'picking_type_id':picking_type.id,
			}
			if o2m_field != 'order_line_ids':
				move_rec.update({'available_to_invoice':False})
			if product.tracking!='none':
				move_rec.update({'move_line_ids':self._create_move_lines(records=matched_related, move=move_rec, qty_field=qty_field)})
			else:
				move_rec.update({'quantity_done':quantity})
			new_moves += Moves.create(move_rec)
			
		
		return new_moves
	

	def _vehicle_must_has_location(self):
		if self.sudo().vehicle_id.location_id.id==False:
			raise UserError(_("Vehicle %s truced as Location!") % (self.sudo().vehicle_id.display_name))
		# elif not self.sudo().vehicle_id.location_id.usage=='transit':
		# 	raise UserError(_("Vehicle %s truced as Location must be TRANSIT Type!") % (self.sudo().vehicle_id.display_name))
	def _generate_materials(self):
		self.ensure_one()
		vals = []
		for this in self.order_line_ids:
			if this.product_id.sale_truck_material_ids:
				for truck_item in this.product_id.sale_truck_material_ids:
					# create truck material
					vals.append({
						'sale_truck_id': self.id,
						'sale_truck_line_id': this.id,
						'partner_id':this.partner_id.id,
						'product_id': truck_item.product_id.id,
						'product_uom_qty': math.ceil(this.product_uom_qty / truck_item.product_qty_master),
						'uom_id': truck_item.product_id.uom_id.id,
						'delivered_qty': this.delivered_qty,
						'rejected_qty': this.rejected_qty})

		SaleTruckMaterial = self.env['sale.order.truck.material']
		if len(vals):
			return SaleTruckMaterial.create(vals)
		else:
			return SaleTruckMaterial

	def _create_picking_to_truck(self):
		Product = self.env['product.product']
		Move = self.env['stock.move']
		MoveLine = self.env['stock.move.line']

		
		picking_type = self.sudo().warehouse_id.sudo().int_type_id

		picking = self.env['stock.picking'].with_user(self.env.company.intercompany_user_id.id).with_context(force_company=self.sudo().plant_id.id).create({'picking_type_id': picking_type.sudo().id, 
				'location_id': self.sudo().warehouse_id.lot_stock_id.id,
				'location_dest_id': self.sudo().vehicle_id.sudo().location_id.id, 
				'scheduled_date': fields.Datetime.now(), 
				# 'plant_id': self.sudo().company_id.id, 
				'origin': self.name,
				'company_id':self.sudo().plant_id.id})
		
		self.load_truck_picking_id = picking.id

		# first we need to prepare
		# dispenser_moves = self.with_user(self.env.company.intercompany_user_id.id).with_context(force_company=self.sudo().plant_id.id)._create_moves('truck_dispanser_ids', picking=picking, company_id=self.plant_id, picking_type=picking_type.sudo(), src_location=self.sudo().warehouse_id.lot_stock_id, dest_location=self.sudo().vehicle_id.location_id, ref=self.name, qty_field='qty')

		galon_moves = self.with_user(self.env.company.intercompany_user_id.id).with_context(force_company=self.sudo().plant_id.id)._create_moves('order_line_ids', picking=picking, company_id=self.plant_id, picking_type=picking_type.sudo(), src_location=self.sudo().warehouse_id.lot_stock_id, dest_location=self.sudo().vehicle_id.location_id, ref=self.name, qty_field='product_uom_qty')

		material_moves = self.with_user(self.env.company.intercompany_user_id.id).with_context(force_company=self.sudo().plant_id.id)._create_moves('sale_truck_material_ids', picking=picking, company_id=self.plant_id, picking_type=picking_type.sudo(), src_location=self.sudo().warehouse_id.lot_stock_id, dest_location=self.sudo().vehicle_id.location_id, ref=self.name, qty_field='product_uom_qty')
		# Moves = dispenser_moves+galon_moves+material_moves
		Moves = galon_moves+material_moves
		
		if len(picking)>1:
			raise ValidationError(_("Created Picking Over!Please contact Administrator!"))
		if len(picking)==0:
			raise ValidationError(_("No Picking Created!\nPlease contact Administrator!"))
		
		validating = picking.with_context(force_company=picking.sudo().company_id.id,allowed_company_ids=[picking.sudo().company_id.id]).with_user(picking.sudo().company_id.intercompany_user_id.id).button_validate()
		if type(validating)==dict:
			res_model = validating.get('res_model')
			if res_model == 'stock.immediate.transfer':
				res_id = validating.get('res_id')
				Wizard = self.env['stock.immediate.transfer'].browse(res_id)
				Wizard.process() # process if wizard showed
			else:
				raise ValidationError(_("Error in validating Delivery Order. Ref: {%s} - _create_picking_to_truck")%(validating['res_model']))

	def _check_qty_available(self):
		self.ensure_one()
		# check line
		for line in self.order_line_ids:
			line._check_qty_product()

		for material in self.sale_truck_material_ids:
			material._check_qty_product()
		

	def btn_confirm(self):
		self.ensure_one()
		self.order_line_ids.check_lot_uom_qty()
		self._check_qty_available()
		if self.receive_material==False:
			self._vehicle_must_filled()
			self._vehicle_must_has_location()
			# prepare moves
			self._create_picking_to_truck()
		self.write({"state":'confirmed'})

	

	def btn_take_confirm(self):
		
		vals = {
			'warehouse_id': self.env.user.company_id.warehouse_id.id,
			'plant_id': self.env.user.company_id.id,
			'state':'submited',
		}
		self.write(vals)
		# self.btn_confirm()

	def _check_balance(self):
		msgs = []
		galon_not_balance = self.order_line_ids.filtered(lambda r:r.product_uom_qty != (r.delivered_qty+r.rejected_qty))
		if len(galon_not_balance):
			msgs.append("%s" % ("\n".join(galon_not_balance.mapped(lambda r:"%s - %s" % (r.product_id.display_name, r.partner_id.display_name,))),))
		
		self.sale_truck_material_ids._check_balance()
		dispenser_no_balance = self.truck_dispanser_ids.filtered(lambda r:r.qty != (r.sent_qty+r.return_qty))
		if len(dispenser_no_balance):
			msgs.append("%s" % ("\n".join(dispenser_no_balance.mapped(lambda r:"%s" % (r.product_id.display_name, ))),))


		if len(msgs):
			msgs.insert(0, "There's not balance qty. Please Check:\n\n")
			raise UserError("\n".join(msgs))


	def _create_picking_rejected(self):

		rejected_qty = sum(self.mapped(lambda r:sum(r.truck_dispanser_ids.mapped('return_qty')))) + sum(self.mapped(lambda r:sum(r.order_line_ids.mapped('rejected_qty'))))


		if rejected_qty:
			Product = self.env['product.product']
			Move = self.env['stock.move']
			MoveLine = self.env['stock.move.line']

			
			picking_type = self.sudo().warehouse_id.sudo().int_type_id

			picking = self.env['stock.picking'].with_user(self.env.company.intercompany_user_id.id).with_context(force_company=self.sudo().plant_id.id).create({'picking_type_id': picking_type.sudo().id, 
					'location_dest_id': self.sudo().warehouse_id.lot_stock_id.id,
					'location_id': self.sudo().vehicle_id.sudo().location_id.id, 
					'scheduled_date': fields.Datetime.now(), 
					# 'plant_id': self.sudo().company_id.id, 
					'origin': self.name,
					'company_id':self.sudo().plant_id.id,
					'carrier_type': 'partner' if self.order_pickup_method_id.name == 'Take in Plant' else 'internal'})
			
			

			# first we need to prepare
			# dispenser_moves = self.with_user(self.env.company.intercompany_user_id.id).with_context(force_company=self.sudo().plant_id.id)._create_moves('truck_dispanser_ids', picking=picking, company_id=self.plant_id, picking_type=picking_type.sudo(), dest_location=self.sudo().warehouse_id.lot_stock_id, src_location=self.sudo().vehicle_id.location_id, ref=self.name, qty_field='return_qty')

			galon_moves = self.with_user(self.env.company.intercompany_user_id.id).with_context(force_company=self.sudo().plant_id.id)._create_moves('order_line_ids', picking=picking, company_id=self.plant_id, picking_type=picking_type.sudo(), dest_location=self.sudo().warehouse_id.lot_stock_id, src_location=self.sudo().vehicle_id.location_id, ref=self.name, qty_field='rejected_qty')

			material_moves = self.with_user(self.env.company.intercompany_user_id.id).with_context(force_company=self.sudo().plant_id.id)._create_moves('sale_truck_material_ids', picking=picking, company_id=self.plant_id, picking_type=picking_type.sudo(), dest_location=self.sudo().warehouse_id.lot_stock_id, src_location=self.sudo().vehicle_id.location_id, ref=self.name, qty_field='rejected_qty')
			# Moves = dispenser_moves+galon_moves+material_moves
			Moves = galon_moves+material_moves

			# Moves._action_confirm()
			
			if len(picking)>1:
				raise ValidationError(_("Created Picking Over!Please contact Administrator!"))
			if len(picking)==0:
				raise ValidationError(_("No Picking Created!\nPlease contact Administrator!"))
			
			validating = picking.with_context(force_company=picking.sudo().company_id.id,allowed_company_ids=[picking.sudo().company_id.id]).with_user(picking.sudo().company_id.intercompany_user_id.id).button_validate()
			if type(validating)==dict:
				res_model = validating.get('res_model')
				if res_model == 'stock.immediate.transfer':
					res_id = validating.get('res_id')
					Wizard = self.env['stock.immediate.transfer'].browse(res_id)
					Wizard.process() # process if wizard showed
					return picking
				else:
					raise ValidationError(_("Error in validating Delivery Order. Ref: {%s} -- _create_picking_rejected")%(validating['res_model']))
			return picking

	def _create_received_to_transit(self):

		Product = self.env['product.product']
		Move = self.env['stock.move']
		MoveLine = self.env['stock.move.line']

		
		picking_type = self.sudo().warehouse_id.sudo().out_type_id
		virtual_location = self.env.ref('stock.stock_location_locations_virtual')
		transit_location_id = self.env['stock.location'].with_user(self.env.user.company_id.intercompany_user_id.id).search([('usage','=','transit'),('company_id','=',False),('location_id','=',virtual_location.id)])	
		# raise ValidationError(_(transit_location_id.name))
		picking = self.env['stock.picking'].with_user(self.env.company.intercompany_user_id.id).with_context(force_company=self.sudo().plant_id.id).create({'picking_type_id': picking_type.sudo().id, 
				'location_dest_id': transit_location_id.id,
				'location_id': self.sudo().vehicle_id.location_id.id,
				'scheduled_date': fields.Datetime.now(), 
				# 'plant_id': self.sudo().company_id.id, 
				'origin': self.name,
				'company_id':self.sudo().plant_id.id,
				'carrier_type': 'partner' if self.order_pickup_method_id.name == 'Take in Plant' else 'internal'})
		
		print ("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")

		# first we need to prepare
		dispenser_moves = self.with_user(self.env.company.intercompany_user_id.id).with_context(force_company=self.sudo().plant_id.id)._create_moves('truck_dispanser_ids', picking=picking, company_id=self.plant_id, picking_type=picking_type.sudo(), dest_location=transit_location_id, src_location=self.sudo().vehicle_id.location_id, ref=self.name, qty_field='sent_qty')

		galon_moves = self.with_user(self.env.company.intercompany_user_id.id).with_context(force_company=self.sudo().plant_id.id)._create_moves('order_line_ids', picking=picking, company_id=self.plant_id, picking_type=picking_type.sudo(), dest_location=transit_location_id, src_location=self.sudo().vehicle_id.location_id, ref=self.name, qty_field='delivered_qty')

		material_moves = self.with_user(self.env.company.intercompany_user_id.id).with_context(force_company=self.sudo().plant_id.id)._create_moves('non_return_sale_truck_material_ids', picking=picking, company_id=self.plant_id, picking_type=picking_type.sudo(), dest_location=transit_location_id, src_location=self.sudo().vehicle_id.location_id, ref=self.name, qty_field='delivered_qty')
		Moves = dispenser_moves+galon_moves+material_moves

		# Moves._action_confirm()
		
		if len(picking)>1:
			raise ValidationError(_("Created Picking Over!Please contact Administrator!"))
		if len(picking)==0:
			raise ValidationError(_("No Picking Created!\nPlease contact Administrator!"))
		
		validating = picking.with_context(force_company=picking.sudo().company_id.id,allowed_company_ids=[picking.sudo().company_id.id]).with_user(picking.sudo().company_id.intercompany_user_id.id).button_validate()
		if type(validating)==dict:
			res_model = validating.get('res_model')
			if res_model == 'stock.immediate.transfer':
				res_id = validating.get('res_id')
				Wizard = self.env['stock.immediate.transfer'].browse(res_id)
				Wizard.process() # process if wizard showed
				return picking
			else:
				raise ValidationError(_("Error in validating Delivery Order. Ref: {%s} -- _create_received_to_transit")%(validating['res_model']))
		return picking
	
	def _create_received_to_company(self):

		Product = self.env['product.product']
		Move = self.env['stock.move']
		MoveLine = self.env['stock.move.line']

		
		picking_type = self.sudo().company_id.warehouse_id.sudo().in_type_id
		transit_location_id = self.env['stock.location'].with_user(self.env.user.company_id.intercompany_user_id.id).search([('usage','=','transit'),('company_id','=',False)])

		location_dest_id = self.sudo().company_id.warehouse_id.lot_stock_id
		if self.plant_id.id==self.company_id.id:
			# if same
			location_dest_id = self.sudo().warehouse_id.lot_stock_id
		
		picking = self.env['stock.picking'].with_user(self.env.company.intercompany_user_id.id).with_context(force_company=self.sudo().company_id.id).create({'picking_type_id': picking_type.sudo().id, 
				'location_id': transit_location_id.id,
				'location_dest_id': location_dest_id.id,
				'scheduled_date': fields.Datetime.now(), 
				# 'plant_id': self.sudo().company_id.id, 
				'origin': self.name,
				'company_id':self.sudo().company_id.id,
				'carrier_type': 'partner' if self.order_pickup_method_id.name == 'Take in Plant' else 'internal'})
		
		

		# first we need to prepare
		dispenser_moves = self.with_user(self.env.company.intercompany_user_id.id).with_context(force_company=self.sudo().company_id.id)._create_moves('truck_dispanser_ids', picking=picking, company_id=self.sudo().company_id, picking_type=picking_type.sudo(), dest_location=self.sudo().company_id.warehouse_id.lot_stock_id, src_location=transit_location_id, ref=self.name, qty_field='sent_qty')

		galon_moves = self.with_user(self.env.company.intercompany_user_id.id).with_context(force_company=self.sudo().company_id.id)._create_moves('order_line_ids', picking=picking, company_id=self.sudo().company_id, picking_type=picking_type.sudo(), dest_location=self.sudo().company_id.warehouse_id.lot_stock_id, src_location=transit_location_id, ref=self.name, qty_field='delivered_qty')

		material_moves = self.with_user(self.env.company.intercompany_user_id.id).with_context(force_company=self.sudo().company_id.id)._create_moves('non_return_sale_truck_material_ids', picking=picking, company_id=self.sudo().company_id, picking_type=picking_type.sudo(), dest_location=self.sudo().company_id.warehouse_id.lot_stock_id, src_location=transit_location_id, ref=self.name, qty_field='delivered_qty')
		Moves = dispenser_moves+galon_moves+material_moves

		# Moves._action_confirm()
		
		if len(picking)>1:
			raise ValidationError(_("Created Picking Over!Please contact Administrator!"))
		if len(picking)==0:
			raise ValidationError(_("No Picking Created!\nPlease contact Administrator!"))
		
		validating = picking.with_context(force_company=picking.sudo().company_id.id,allowed_company_ids=[picking.sudo().company_id.id]).with_user(picking.sudo().company_id.intercompany_user_id.id).button_validate()
		if type(validating)==dict:
			res_model = validating.get('res_model')
			if res_model == 'stock.immediate.transfer':
				res_id = validating.get('res_id')
				Wizard = self.env['stock.immediate.transfer'].browse(res_id)
				Wizard.process() # process if wizard showed
				return picking
			else:
				raise ValidationError(_("Error in validating Delivery Order. Ref: {%s} -- _create_received_to_company")%(validating['res_model']))
		picking.with_context(force_company=picking.sudo().company_id.id,allowed_company_ids=[picking.sudo().company_id.id]).with_user(picking.sudo().company_id.intercompany_user_id.id).btn_sent()
		return picking


	def _create_receiving_return_to_plant(self):
		self.ensure_one()
		return_qty = sum(self.mapped(lambda r:sum(r.sale_truck_material_ids.mapped('return_qty'))))


		if return_qty:
			Product = self.env['product.product']
			Move = self.env['stock.move']
			MoveLine = self.env['stock.move.line']

			
			picking_type = self.sudo().warehouse_id.sudo().in_type_id
			src_location = self.env.ref('stock.stock_location_customers')

			picking = self.env['stock.picking'].with_user(self.env.company.intercompany_user_id.id).with_context(force_company=self.sudo().plant_id.id).create({
					'picking_type_id': picking_type.sudo().id, 
					'location_dest_id': self.sudo().warehouse_id.lot_stock_id.id,
					'location_id': src_location.id, 
					'scheduled_date': fields.Datetime.now(), 
					# 'plant_id': self.sudo().company_id.id, 
					'origin': self.name,
					'company_id':self.sudo().plant_id.id,
					'carrier_type': 'partner' if self.order_pickup_method_id.name == 'Take in Plant' else 'internal'})
			
			
			material_moves = self.with_user(self.env.company.intercompany_user_id.id).with_context(force_company=self.sudo().plant_id.id)._create_moves('return_sale_truck_material_ids', picking=picking, company_id=self.plant_id, picking_type=picking_type.sudo(), dest_location=self.sudo().warehouse_id.lot_stock_id, src_location=src_location, ref=self.name, qty_field='return_qty')
			Moves = material_moves

			# Moves._action_confirm()
			
			if len(picking)>1:
				raise ValidationError(_("Created Picking Over!Please contact Administrator!"))
			if len(picking)==0:
				raise ValidationError(_("No Picking Created!\nPlease contact Administrator!"))
			
			validating = picking.with_context(force_company=picking.sudo().company_id.id,allowed_company_ids=[picking.sudo().company_id.id]).with_user(picking.sudo().company_id.intercompany_user_id.id).button_validate()
			if type(validating)==dict:
				res_model = validating.get('res_model')
				if res_model == 'stock.immediate.transfer':
					res_id = validating.get('res_id')
					Wizard = self.env['stock.immediate.transfer'].browse(res_id)
					Wizard.process() # process if wizard showed
					return picking
				else:
					raise ValidationError(_("Error in validating Delivery Order. Ref: {%s} -- _create_receiving_return_to_plant")%(validating['res_model']))
			return picking

	def _create_move_lines_lot(self, records, move, qty_field):
		self.ensure_one()
		MoveLine = self.env['stock.move.line']

		# move_lines = MoveLine
		move_lines = []
		for rec in records:
			err=True
			try:
				has_lot_ids = getattr(rec, 'lot_ids')
				err=False
			except Exception as e:
				has_lot_ids = False
			
			if not err:
				if not len(has_lot_ids):
					raise UserError(_("Please Select Lot for %s" % (rec.product_id.display_name,)))
				# if not err
				# it has has_lot_ids
				for lot in has_lot_ids.sudo():
					lot = lot.sudo()
					Lot = self.env['stock.production.lot'].sudo().with_context(force_company=move.company_id.id,allowed_company_ids=move.company_id.ids).search([('product_id','=',rec.product_id.id), ('name','=',lot.lot_id.name),('company_id','=',move.company_id.id)])
					if not len(Lot):
						Lot = self.env['stock.production.lot'].create({
							'name':lot.lot_id.name,
							'company_id':move.company_id.id,
							'product_id':rec.product_id.id
						})

					new_rec = dict(product_id=rec.product_id.id, 
							picking_id=move.picking_id.id,
							product_uom_id=rec.product_id.uom_id.id, 
							lot_id=Lot.sudo().id,
							qty_done=getattr(lot, qty_field),
							# product_uom_qty=getattr(lot, qty_field),
							location_id=move.location_id.id, 
							location_dest_id=move.location_dest_id.id, 
							company_id=move.company_id.id)
					# move_lines += MoveLine.create(new_rec)
					move_lines.append((0, 0, new_rec))
			else:
				Lot = rec.sudo().lot_id
				find_lot = self.env['stock.production.lot'].sudo().with_context(force_company=move.company_id.id,allowed_company_ids=move.company_id.ids).search([('product_id','=',rec.product_id.id), ('name','=',rec.sudo().lot_id.name),('company_id','=',move.get('company_id'))])
				if not len(find_lot):
					Lot = self.env['stock.production.lot'].create({
						'name':rec.sudo().lot_id.name,
						'company_id':move.company_id.id,
						'product_id':rec.product_id.id
					})

				new_rec = dict(product_id=rec.product_id.id, 
						picking_id=move.picking_id.id,
						product_uom_id=rec.product_id.uom_id.id, 
						lot_id=Lot.id,
						qty_done=getattr(rec, qty_field),
						
						location_id=move.location_id.id, 
						location_dest_id=move.location_dest_id.id, 
						company_id=move.company_id.id)
				# move_lines += MoveLine.create(new_rec)
				move_lines.append((0, 0, new_rec))
		return move_lines

	def btn_post(self):
		self.ensure_one()
		self._check_balance()
		self.order_line_ids._check_balance()
		
		user = self.env.user
		self.order_line_ids._check_balance()

		picking = self.env['stock.picking']
		sale_order = self.env['sale.order'].with_user(self.env.user.company_id.intercompany_user_id.id)
		picking_ids = []
		product = self.env['product.product']
		domain = [('code', '=', 'internal'), ('company_id', '=', self.plant_id.id)]
		picking_type = self.env['stock.picking.type'].with_user(self.env.user.company_id.intercompany_user_id.id).search(domain, limit=1)
		transit_location_id = self.env['stock.location'].with_user(self.env.user.company_id.intercompany_user_id.id).search([('usage','=','transit'),('company_id','=',False)])

		picking_returned = self._create_receiving_return_to_plant()
		if picking_returned and len(picking_returned):
			self.update({
				'return_material_picking':picking_returned.id,
			})
		
		if self.receive_material==False:
			# create internal transfer for qty rejected
			# picking_rejected = self.create_rejected(picking_type)
			picking_rejected = self._create_picking_rejected()
			
			
			# create internal transfer for qty received
			# picking_received_to_transit = self.create_received_to_transit(transit_location_id)
			picking_received_to_transit = self._create_received_to_transit() 
			

			# picking_received_to_company = self._create_received_to_company() ## commented on 2020/06/17 -> change with receiving from created intercompany purchase order
			self.update({
				'transit_out_picking_id':picking_received_to_transit.id,
				# 'transit_in_picking_id':picking_received_to_company.id, ## commented on 2020/06/17 -> change with receiving from created intercompany purchase order
			})

		

			if picking_rejected and len(picking_rejected):
				self.update({'rejecting_picking_id':picking_rejected.id,})

			# creating so->intercompany purchase->receiving
			if self.company_id.id != self.plant_id.id:
				# only create interco purchase when plant != company
				self._create_interco_purchase()
			
				
			
			# if picking_received_to_transit and picking_received_to_company: ## commented on 2020/06/17 -> change with receiving from created intercompany purchase order
			if picking_received_to_transit:
				# create sale order
				domain = [('active','=',True),('price_unit_discount_agreement','=',False)]
				pickup_methode = self.env['order.pickup.method'].search(domain, limit=1)
				ids_line = self.order_line_ids
				ids_partner = self.order_line_ids.mapped('partner_id')
				ids_dispanser = self.truck_dispanser_ids.filtered(lambda r:r.sent_qty>0.0)
				sos = []
				for dt_partner in ids_partner:
					header = []
					footer = []

					for this in ids_dispanser:
						# dispanser exist
						partner_dt = this.truck_dispanser_line_ids.filtered(lambda p: p.partner_id.id == dt_partner.id)
						if len(partner_dt):
							
							quan = [customer.qty for customer in partner_dt]
							qty = sum(quan)
							val_line = {'product_id': this.product_id.id,
										'name': this.sale_truck_id.name,
										
										'product_uom': this.uom_id.id,
										'price_unit': 0.0,
										'tax_id': [(6, 0, this.product_id.taxes_id.ids)], }
							footer.append((0, 0, val_line))
							
					for this in ids_line.filtered(lambda r:r.partner_id.id==dt_partner.id):
						# truck line exist
						if this.delivered_qty > 0:
							tax = 0
							qty = this.delivered_qty
							for dt_tax in this.product_id.taxes_id:
								tax = tax + (dt_tax.amount / 100.0)
							val_line = {'product_id': this.product_id.id,
										'name': this.sale_truck_id.name,
										'product_uom_qty': qty,
										'product_uom': this.uom_id.id,
										'discount_fixed_line':this.discount_fixed_line,
										'price_unit': this.price_unit,
										'tax_id': [(6, 0, this.product_id.taxes_id.ids)],}
							
							footer.append((0, 0, val_line))
						for dt_material in this.sale_truck_material_ids:
							# material product exist
							if this.delivered_qty > 0:
								tax = 0
								qty = dt_material.delivered_qty
								for dt_tax in dt_material.product_id.taxes_id:
									tax = tax + (dt_tax.amount / 100)
								val_line = {'product_id': dt_material.product_id.id,
											'name': dt_material.sale_truck_id.name,
											'product_uom_qty': qty,
											'product_uom': dt_material.uom_id.id,
											'price_unit': 0.0,
											'tax_id': [(6, 0, dt_material.product_id.taxes_id.ids)], }
								footer.append((0, 0, val_line))
					partner_pricelist = dt_partner.sudo().partner_pricelist_ids.filtered(lambda r:r.team_id.id==self.team_id.id)
					if len(partner_pricelist)!=1:
						raise ValidationError(_("%s tidak mempunyai pricelist untuk team %s") % (dt_partner.display_name, self.sudo().team_id.display_name,))

					if partner_pricelist.sudo().pricelist_id.id==False:
						raise ValidationError(_("%s pada pricelist divisi %s belum didefinisikan kolom pricelistnya!") % (dt_partner.display_name, self.sudo().team_id.display_name, ))

					warehouse = self.sudo().company_id.warehouse_id
					if self.sudo().company_id.id == self.sudo().plant_id.id:
						# if same company
						# use self.warehouse_id
						warehouse = self.warehouse_id


					header = {'partner_id': dt_partner.id, 
								'sale_truck_id': self.id,
								'date_order': datetime.now(),
								'order_line': footer,
								'vehicle_model_id': self.vehicle_id.model_id.id,
								'interco_master': False,
								'auto_generated':True,
								'order_pickup_method_id': pickup_methode.id,
								'team_id': self.sudo().team_id.id,
								'warehouse_id':warehouse.id,
								'company_id':self.sudo().company_id.id,
								'pricelist_id':partner_pricelist.sudo().pricelist_id.id,
								}
					sos.append(header)
				created_so = self.env['sale.order']
				# sos -> so Source COmpany with partner = Customer
				# loop each sos
				for val_so in sos:
					sale_order_id = sale_order.sudo().create(val_so)
					sale_order_id = sale_order_id.sudo()
					created_so += sale_order_id
					sale_order_id.with_context(force_company=self.sudo().company_id.id, allowed_company_ids=[self.sudo().company_id.id,self.env.user.company_id.id]).sudo().action_confirm()
					
					for m_picking in sale_order_id.picking_ids:
						#Fardan Salah Lokasi..:D
						virtual_location = self.env.ref('stock.stock_location_locations_virtual')
						transit_location_id = self.env['stock.location'].with_user(self.env.user.company_id.intercompany_user_id.id).search([('usage','=','transit'),('company_id','=',False),('location_id','=',virtual_location.id)])	

						m_picking.move_line_ids.unlink()
						m_picking.location_id = transit_location_id.id
						for m_move in m_picking.move_ids_without_package:
							sale_truck_id = m_picking.sale_id.sale_truck_id
							matched_related = getattr(self, 'order_line_ids').filtered(lambda r: r.product_id == m_move.product_id and r.partner_id.id == sale_order_id.partner_id.id)
							if not matched_related:
								matched_related = getattr(self, 'sale_truck_material_ids').filtered(lambda r: r.product_id == m_move.product_id and r.partner_id.id== sale_order_id.partner_id.id)
							if m_move.product_id.tracking!='none':
								
								m_move.update({
									'move_line_ids':self._create_move_lines_lot(
										records=matched_related, 
										move=m_move, qty_field='delivered_qty')})

							else:
								m_move.quantity_done = m_move.product_uom_qty
						validating = m_picking.button_validate()
						m_picking.fleet_vehicle_id = self.vehicle_id
						m_picking.fleet_driver_id = self.vehicle_driver_id
												
						
	  	

						if type(validating)==dict:
							res_model = validating.get('res_model')
							if res_model == 'stock.immediate.transfer':
								res_id = validating.get('res_id')
								Wizard = self.env['stock.immediate.transfer'].browse(res_id)
								
								Wizard.sudo().process() # process if wizard showed
								
							else:
								raise ValidationError(_("Error in validating Delivery Order. Ref: {%s} -- POST")%(validating['res_model']))
						
						picking_ids.append(m_picking.id)

				if created_so and len(created_so):
					created_so.sudo().write({
						'interco_master': True,
						'plant_id': self.sudo().plant_id.id,
						'interco_company_id': self.sudo().plant_id.id,
					})
					
				
		self.write({'state':'done'})
		return picking_ids

	def _prepare_interco_purchase_line(self, purchase, line):
		self.ensure_one()

		def apply_onchange(new_obj, skips = []):
			for field_name,mthds in new_obj._onchange_methods.items():
				if field_name not in skips:
					new_obj._onchange_eval(field_name,'1',{})
			return new_obj

		# prepare object first
		data = {
			'order_id':purchase.id,
			'product_id':line.product_id.id,
		}
		new_obj = self.env['purchase.order.line'].new(data)
		
		new_obj = apply_onchange(new_obj) # apply onchange --> all method

		datas = []
		for line in picking_line_id:
			new_obj.update({
				'product_uom_qty':line.interco_move_line_qty_done,
				'product_qty':line.interco_move_line_qty_done,
				'price_unit':so_line.sudo().price_unit,
				})
			new_obj = apply_onchange(new_obj.sudo(), ['product_id']) #apply onchange without onchange product_id
			to_write = new_obj._convert_to_write({name: new_obj[name] for name in new_obj._cache})
			datas.append(to_write)
		return datas


	def _prepare_so_line_for_so_truck(self, Order, Product):
		self.ensure_one()

		def apply_onchange(new_obj, skips = []):
			for field_name,mthds in new_obj._onchange_methods.items():
				if field_name not in skips:
					new_obj._onchange_eval(field_name,'1',{})
			return new_obj
		res = {}

		# intercompany_pricelist = self.env['inter.company.pricelist'].get_intercompany_pricelist(company=self.sudo().plant_id,partner=self.sudo().company_id.partner_id)

		# find sum of product in order_line_ids
		lines = self.order_line_ids.filtered(lambda r:r.product_id.id==Product.id)
		price = self.env['inter.company.pricelist'].get_product_fixed_price(self.plant_id,self.company_id.partner_id,lines.product_id)

		if len(lines):
			delivered = sum(lines.mapped('delivered_qty'))
			Sol = self.env['sale.order.line']

			

			data = {
				'order_id':Order.id,
				'product_id':Product.id,
				'product_uom_qty':delivered,
				'product_uom':Product.uom_id.id,
				
				'state':'draft'
			}
			obj = Sol.new(data)
			
			apply_onchange(obj, [])

			obj.update({'price_unit':price})
			obj._onchange_discount()
		
		res = obj._convert_to_write({name: obj[name] for name in obj._cache})
		
		return res
	
	def _confirm_purchase(self, Purchase):
		Purchase = Purchase.with_context(allowed_company_ids=Purchase.company_id.ids,force_company=Purchase.company_id.id)
		if Purchase.state=='to approve':
			Purchase.sudo().button_approve()

		for picking in Purchase.picking_ids:
			if len(picking.move_line_ids):
				picking.move_line_ids.unlink()
			for move in picking.move_lines:
				# find all related so truck line with same product
				# will result multiple records on various partners
				sotrucklines = self.env['sale.order.truck.line'].search([('sale_truck_id','=',self.id),('product_id','=',move.product_id.id)])
				# get all lots
				allLotLines = sotrucklines.mapped('lot_ids')
				# if lot
				if len(allLotLines):
					# group/loop by lot
					grouped_lots = allLotLines.mapped('lot_id')
					# loop each grouped_lots
					for lot in grouped_lots:

						lot = lot.sudo()
						# find lot in target company
						Lot = self.env['stock.production.lot'].sudo().with_context(force_company=picking.company_id.id,allowed_company_ids=picking.company_id.ids).search([('product_id','=',move.sudo().product_id.id), ('name','=',lot.name),('company_id','=',move.company_id.id)])
						# if not found
						if not len(Lot):
							# create new lot on target company
							Lot = self.env['stock.production.lot'].create({
								'name':lot.name,
								'company_id':picking.sudo().company_id.id,
								'product_id':move.sudo().product_id.id
							})
						lotLines = allLotLines.filtered(lambda r:r.sudo().lot_id.id==lot.sudo().id)
						# get sum qty of sale.order.truck.line.lot
						lot_qty = sum(lotLines.mapped(lambda r:r.delivered_qty)) #get qty from delivered qty
						if lot_qty>0.0:
							new_rec = dict(product_id=move.sudo().product_id.id,
									picking_id=picking.sudo().id,
									product_uom_id=move.sudo().product_id.uom_id.id, 
									lot_id=Lot.sudo().id,
									qty_done=lot_qty,
									location_id=move.sudo().location_id.id, 
									location_dest_id=move.sudo().location_dest_id.id, 
									company_id=move.company_id.id)
							
							move.update({
								'move_line_ids':[(0,0,new_rec)]
							})
						# end if has lots
				else:
					# IF NOT HAS LOT IDS
					pass # do nothing


					
			validating = picking.button_validate()

			if type(validating)==dict:
				res_model = validating.get('res_model')
				if res_model == 'stock.immediate.transfer':
					res_id = validating.get('res_id')
					Wizard = self.env['stock.immediate.transfer'].browse(res_id)
					Wizard.process() # process if wizard showed
				else:
					raise ValidationError(_("Error in validating Delivery Order when post Sale Order Truck. Ref: {%s}")%(validating['res_model']))

	def _create_plant_sale_order(self):
		team = self.sudo().team_id.id
		# finding team in company
		team = self.env['crm.team'].with_context(allowed_company_ids=self.sudo().plant_id.ids).search([('company_id','=',self.sudo().plant_id.id), ('name','=',self.sudo().team_id.name)])
		if not len(team):
			raise ValidationError(_("Failed to Finding team \"%s\" on \"%s\" ") % (self.sudo().team_id.display_name, self.sudo().plant_id.display_name))

		# self.env['inter.company.pricelist'].get_product_fixed_price(self.plant_id,purchase.company_id.partner_id,so_line.product_id),
		# self.env['inter.company.pricelist'].get_intercompany_pricelist(company=company,partner=partner)
		


		new_sale = {
			'company_id':self.sudo().plant_id.id,
			'partner_id':self.sudo().company_id.partner_id.id,
			'team_id':team.id,
			'vehicle_model_id':self.vehicle_model_id.id,
			'order_pickup_method_id':self.order_pickup_method_id.id,
			'carton_sale':False,
			'date_order_mask':fields.Date.today(),
			'date_order':fields.Datetime.now(),
			'commitment_date_mask':fields.Date.today(),
			'commitment_date':fields.Datetime.now(),
			'validity_date':fields.Date.today(),
			'sale_truck_id':self.id,
			'currency_id':self.currency_id.id,
			
			# 'auto_generated':True,
		}

		SaleOrder = self.env['sale.order']

		NewSale = SaleOrder.sudo().create(new_sale)

		Products = self.order_line_ids.mapped('product_id')
		Lines = []
		for prod in Products:
			Lines.append((0,0,self._prepare_so_line_for_so_truck(NewSale, prod)))

		NewSale.with_context(disable_launch_stock_rule=True).sudo().write({'order_line':Lines})
		NewSale.with_context(plant_confirm=1,force_validating_interco_lot=True, force_approval=True, disable_launch_stock_rule=True, force_request=True) \
			.sudo().action_confirm()

		# get purchase order that created by intercompany rules
		Purchase = self.env['purchase.order'].sudo().search([('auto_sale_order_id','=',NewSale.sudo().id)])
		if not len(Purchase):
			raise ValidationError(_("No Purchase Created for %s. Please contact administrator!") % (self.sudo().display_name,))

		self._confirm_purchase(Purchase)

		
		if len(NewSale.picking_ids) and any(NewSale.picking_ids.mapped(lambda r:r.state in ['assigned'])):
			# unreserve if reserved
			NewSale.sudo().picking_ids.do_unreserve()
		NewSale.sudo().picking_ids.unlink() # delete

		NewSale.sudo().write({'state':'done'}) # force to done
		# update plant_sale_id field so can be accessed on sale order truck
		
		# update picking so it will related to sale.order
		self.transit_out_picking_id.sudo().write({'sale_id':NewSale.id})
		return NewSale
	
	def _create_interco_purchase(self):
		self.ensure_one()
		# create Sale Order
		# so when sale order confirmed will automatically create purchase order in cross company side transaction
		Sale = self.sudo()._create_plant_sale_order()

		Purchase = self.env['purchase.order'].sudo().search([('auto_sale_order_id','=',Sale.sudo().id)])

		self.write({
			'plant_sale_id':Sale.sudo().id,
			'purchase_id':Purchase.sudo().id,
		})

	def btn_cancel(self):
		picking_rejected = self._create_picking_rejected()
		if picking_rejected and len(picking_rejected):
			self.update({'rejecting_picking_id':picking_rejected.id,
							'state':'cancel'})
		else:
			raise UserError('Cannot cancel SOT, no rejected quantity or return quantity!')

	def open_reject_message_wizard(self):
		self.ensure_one()
		
		form = self.env.ref('approval_matrix.message_post_wizard_form_view')
		context = dict(self.env.context or {})
		context.update({'default_prefix_message':"<h4>Cancelling Sale Order Truck</h4>","default_suffix_action": "btn_cancel"}) #uncomment if need append context
		context.update({'active_id':self.id,'active_ids':self.ids,'active_model':'sale.order.truck'})
		res = {
			'name': "%s - %s" % (_('Cancelling Sale Order Truck'), self.name),
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'message.post.wizard',
			'view_id': form.id,
			'type': 'ir.actions.act_window',
			'context': context,
			'target': 'new'
		}
		rejected_qty = sum(self.mapped(lambda r:sum(r.truck_dispanser_ids.mapped('return_qty')))) + sum(self.mapped(lambda r:sum(r.order_line_ids.mapped('rejected_qty'))))
		if rejected_qty:
			return res
		else:
			raise UserError('Cannot cancel SOT, no rejected quantity or return quantity!')