# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime
from odoo.addons import decimal_precision as dp

class StockMove(models.Model):
	""" Inherit model stock.move """
	_inherit = "stock.move"

	pass_qty = fields.Float(digits=dp.get_precision('Product Unit of Measure'),
							copy=False)
	fail_qty = fields.Float(string="Quarantine Qty",
							digits=dp.get_precision('Product Unit of Measure'),
							copy=False)
	fail_reason = fields.Char(string="Quarantine Reason", copy=False)
	check_id = fields.Many2one('stock.quality.check', string="Quality Check")

	
	def print_quality_check_report(self):
		""" show quality check report """
		action = self.env.ref('inward_quality.stock_quality_check_action')
		result = action.read()[0]
		if self.check_id:
			result['domain'] = "[('id','=',%s)]" % self.check_id.id
		return result

class StockMoveLine(models.Model):
	""" Inherit model stock.move.line """
	_inherit = "stock.move.line"

	fail_qty = fields.Float(default=0.0, string="Quarantine Qty",
							digits=dp.get_precision('Product Unit of Measure'))
	is_fail = fields.Boolean(default=False)

class Picking(models.Model):
	""" Inherit stock.picking"""
	_inherit = "stock.picking"



	###ADDED 20 MEI 2020###
	location_id = fields.Many2one(
        'stock.location', "Source Location",
        default=lambda self: self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).default_location_src_id,
        check_company=True, readonly=False, required=True,
        )




	check_active = fields.Boolean(
		related='location_dest_id.check_active',
		readonly=True)

	def rejected_moves(self, line, context=None):
		""" Rejected move """
		#move_line_data = {}
		stock_move_obj = self.env['stock.move']
		stock_move_line_obj = self.env['stock.move.line']
		
		dest_loc_id = self.env.company.rejection_location.id
		
		if not dest_loc_id:
			raise UserError(_('Kindly Configure Rejected Location in Settings.'))
		vals_obj = {
			'name': self.name,
			'picking_id': False,
			'picking_type_id': False,
			'product_id': line.product_id.id,
			'product_uom': line.product_uom.id,
			'product_uom_qty': line.fail_qty,
			'origin': line.product_id.name or '',
			'location_id': self.location_dest_id.id,
			'location_dest_id': dest_loc_id,
			#'move_line_ids': [(0, 0, move_line_data)]
		}
		new_id = stock_move_obj.create(vals_obj)
		for move in line.move_line_ids:
			if move.is_fail:
				package_src = self.env['stock.quant.package'].search([
								('name', '=', move.lot_id.name),
								('location_id', '=', move.location_dest_id.id)], limit=1)

				stock_move_line_obj.create({
					'move_id': new_id.id,
					'reference': self.name,
					'product_id': move.product_id.id,
					'lot_id': move.lot_id.id,
					'product_uom_qty': 0,
					'product_uom_id': move.product_uom_id.id,
					'qty_done': move.fail_qty,
					'location_id': self.location_dest_id.id,
					'location_dest_id': dest_loc_id,
					'package_id':  package_src.id or False,
				})
		new_id._action_done()

	
	def action_done(self):
		""" override action_done function """
		res = super(Picking, self).action_done()
		precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
		if self.check_active:
			for line in self.move_lines:
				if line.fail_qty:
					self.rejected_moves(line, context=None)
				total_qty = line.pass_qty + line.fail_qty
				#Change by ADI - 2021-05-19 ---> line.product_uom_qty > 0
				if line.quantity_done <= 0 and line.product_uom_qty > 0:
					raise UserError(
						_('Done Quantity should be filled in ( ' \
						  + (line.product_id.default_code or '') \
						  + ' ' + (line.product_id.name) + ' )'))
				if not total_qty == round(line.quantity_done, precision):
					raise UserError(
						_('Sum of Pass and Quarantine Qty Should be equal to Done Qty in ( ' \
						  + (line.product_id.default_code or '') \
						  + ' ' + (line.product_id.name) + ' )'))
				if line.fail_qty and not line.fail_reason:
					raise UserError(
						_('There is a quarantine qty in (' + (line.product_id.default_code or '') \
						  + ' ' + (line.product_id.name) \
						  + ') .So Kindly give a quarantine reason.'))
				qc_obj = self.env['stock.quality.check']
				if not line.pass_qty and line.fail_qty:
					qc_state = 'failed'
				elif line.pass_qty and not line.fail_qty:
					qc_state = 'passed'
				elif line.pass_qty and line.fail_qty:
					qc_state = 'partial'
				if line.quantity_done:
					create_vals = {
						'product_id': line.product_id.id,
						'done_qty': line.quantity_done,
						'pass_qty': line.pass_qty,
						'fail_qty': line.fail_qty,
						'product_uom_id': line.product_uom.id,
						'state': qc_state,
						'date': fields.Date.today(),
						'move_id': line.id,
						'reason_of_failure': line.fail_reason,
					}
					new_check_id = qc_obj.create(create_vals)
					if new_check_id:
						line.write({'check_id': new_check_id.id})
		return res
