# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError

import logging
_logger = logging.getLogger(__name__)


class StockIntercoMoveLine(models.Model):
	_name = 'stock.interco.move.line'
	_description = 'Stock Interco Move Line'


	# uncomment if using tracking modules
	#_inherit = ['mail.thread', 'mail.activity.mixin']

	move_id = fields.Many2one('stock.move', string="Moves", required=True)
	product_id = fields.Many2one('product.product', string="Product", related="move_id.product_id", readonly=True)
	picking_id = fields.Many2one('stock.picking', string="Picking", related="move_id.picking_id", store=True, readonly=True)
	
	qty = fields.Float(string="Qty", default=0.0, required=True,digits='Product Unit of Measure')
	
	warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse Location", required=True, default=lambda self:self._default_warehouse())
	
	plant_id = fields.Many2one(related="picking_id.plant_id")

	src_location_id = fields.Many2one('stock.location', string="Stock Location", compute="_compute_src_location_id")
	# takeout function compute untuk default stock location
	# src_location_id = fields.Many2one('stock.location', string="Stock Location")
	
	available_lot_in_location = fields.Many2many('stock.production.lot', compute="_compute_available_lot_in_location", string="Available Lot", context={'all_companies':True})
	lot_id = fields.Many2one('stock.production.lot', string="Lot", required=True)
	free_qty = fields.Float('Free To Use Quantity', compute='_compute_quantities', digits='Product Unit of Measure', store=True)

	_sql_constraints = [
		('unique_lot_id', 'unique(move_id,lot_id)', 'Cannot fill same Lot')
	]

	@api.onchange('lot_id')
	def onchange_lot_id(self):
		print("onchange_lot_id")
		total_qty = 0
		lot_qty = 0.0
		qty = 0.0
		lot_ids = self.move_id.interco_move_line_ids.mapped('lot_id')
		print("lot_ids----------------->",self.move_id.location_id.display_name)
		print("locate_ids----------------->",[x.move_lines for x in self.picking_id])
		for lot in lot_ids:
			line = self.move_id.interco_move_line_ids.filtered(lambda r:r.lot_id.id == lot.id).sorted('qty',reverse=True)
			line = line[0]
			total_qty += line.qty

		if self.lot_id.id:
			
			lot_qty = self._get_lot_free_qty()
			
			if lot_qty <=  self.move_id.product_uom_qty:
				qty = lot_qty
			else:
				qty = self.move_id.product_uom_qty - total_qty
		self.free_qty = lot_qty
		self.qty = qty
		# self.update(dict(free_qty=lot_qty,qty=qty))
		# fix me
		# return {'domain':{'lot_id':[('id','not in',lot_ids.ids),('product_id','=',self.move_id.product_id.id),('company_id','=',self.picking_id.plant_id.id)]}} 

	@api.onchange('move_id')
	def _onchange_move_id(self):
		print("_onchange_move_id")
		if self.move_id:
			self.warehouse_id = self.move_id.picking_id.plant_id.id

	def _get_lot_free_qty(self):
		print("_get_lot_free_qty")
		self.ensure_one()
		# context = self._context.copy()
		# context.update({'allowed_company_ids':self.sudo().plant_id.ids, 'lot_id':self.sudo().lot_id.id})
		# res =  self.with_context(context).with_user(self.env.company.intercompany_user_id.id).lot_id.product_qty
		context = self._context.copy()
		context.update({'allowed_company_ids':self.sudo().plant_id.ids, 'lot_id':self.sudo().lot_id.id})
		quant = self.with_context(context).with_user(self.env.company.intercompany_user_id.id).\
				env['stock.quant'].search([('product_id', '=', self.product_id.id),
											('location_id', '=', self.src_location_id.id),
											('lot_id', '=', self.sudo().lot_id.id)])
		res = quant.quantity
		return res

	@api.depends('lot_id')
	def _compute_quantities(self):
		print("_compute_quantities")
		for rec in self:
			res = 0.0
			if rec.move_id.id and rec.lot_id.id:
				res = rec._get_lot_free_qty()
			rec.free_qty = res

	
	@api.onchange('src_location_id')
	def onchange_src_location_id(self):
		print("onchange_src_location_id")
		self._compute_available_lot_in_location()
	
	@api.constrains('lot_id','move_id')
	def constrains_lot_move(self):
		print("constrains_lot_move")
		for rec in self:
			# find duplicate lot_id on same move_id
			browse = self.search([('move_id','=',rec.move_id.id), ('lot_id','=',rec.lot_id.id), ('id','!=',rec.id)])
			if len(browse):
				raise UserError(_("Couldn't defining duplicate lot on same product demand movement!\nPlease check %s / %s") % (rec.product_id.display_name, rec.lot_id.display_name,))

	@api.depends('src_location_id','move_id')
	def _compute_available_lot_in_location(self):
		print("_compute_available_lot_in_location")
		
		Lot = self.env['stock.production.lot']

		for rec in self.sudo():
			
			context = dict(force_company=rec.warehouse_id.company_id.id, allowed_company_ids=rec.warehouse_id.company_id.ids)
			ProductLot = Lot.with_user(rec.move_id.company_id.intercompany_user_id.id).with_context(context).search([('product_id','=',rec.product_id.id), ('company_id','=',rec.warehouse_id.company_id.id)])
			AvailableLot = self.env['stock.production.lot'].with_context(context)
			ProductProduct = self.env['product.product'].search([('id','in',ProductLot.mapped('product_id.id'))])
			quant_ids = self.env['stock.quant'].search([('product_id', '=', rec.product_id.id),
														('location_id', '=', rec.src_location_id.id)])
			for quant in quant_ids:
				available = quant.quantity
				if available > 0.0:
					AvailableLot += quant.lot_id

			rec.update({
				'available_lot_in_location':[(6,None, AvailableLot.ids)]
				})

	# @api.depends('src_location_id','move_id')
	# def _compute_available_lot_in_location(self):
		
	# 	Lot = self.env['stock.production.lot']

	# 	for rec in self.sudo():
			
	# 		context = dict(force_company=rec.warehouse_id.company_id.id, allowed_company_ids=rec.warehouse_id.company_id.ids)
	# 		ProductLot = Lot.with_user(rec.move_id.company_id.intercompany_user_id.id).with_context(context).search([('product_id','=',rec.product_id.id), ('company_id','=',rec.warehouse_id.company_id.id)]).filtered(lambda r:r.product_qty>0.0)
	# 		AvailableLot = self.env['stock.production.lot'].with_context(context)
	# 		ProductProduct = self.env['product.product'].search([('id','in',ProductLot.mapped('product_id.id'))])
			
	# 		for lot in ProductLot:
	# 			ProductLotInLocation = ProductProduct.with_context(dict(location=rec.src_location_id.id, lot_id=lot.id))
	# 			if ProductLotInLocation.qty_available > 0.0:
	# 				AvailableLot += lot
			
			

	# 		rec.update({
	# 			'available_lot_in_location':[(6,None, AvailableLot.ids)]
	# 			})


	@api.depends('warehouse_id','lot_id')
	def _compute_src_location_id(self):
		print("_compute_src_location_id")
		for rec in self:
			if rec.warehouse_id.id:
				rec.src_location_id = rec.with_user(1).warehouse_id.lot_stock_id.id
			# if rec.lot_id:
			# 	rec.src_location_id = rec.lot_id.quant_ids.location_id.filtered(lambda x:x.company_id.id == self.move_id.picking_id.plant_id.id and x.usage == 'internal')[0]
				# print("src_location_id",rec.src_location_id.id)
			else:
				rec.src_location_id = self.env['stock.location']
				
	def _default_warehouse(self):
		print("_default_warehouse")
		if self.move_id.id:
			self.warehouse_id = self.move_id.picking_id.plant_id.id

	@api.constrains('qty')
	def constrains_qty(self):
		print("constrains_qty")
		for rec in self:
			# check if qty greater than demand
			if rec.qty <= 0.0:
				raise ValidationError(_("Qty must be greater than 0"))
			elif rec.qty>rec.move_id.product_uom_qty:
				raise ValidationError(_("Selected Lot for %s greater than Demand Qty on lot %s") % (rec.product_id.display_name,rec.lot_id.display_name,))

			if rec.qty>rec.free_qty:
				raise ValidationError(_("Qty Over than Available (%s)") % (rec.lot_id.display_name,))
		
		moves = self.mapped('move_id')
		for move in moves:
			demand = move.product_uom_qty
			take_qty = sum(move.interco_move_line_ids.mapped('qty'))
			if take_qty>demand:
				raise ValidationError(_("Total qty to take greater than the demand.\nDemand: %s Total Defined Qty:%s") % (demand, take_qty))