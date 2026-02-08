# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from datetime import datetime
from dateutil import relativedelta
from itertools import groupby
from operator import itemgetter
from re import findall as regex_findall, split as regex_split

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
from odoo.exceptions import UserError,ValidationError

import logging
_logger = logging.getLogger(__name__)


class StockMove(models.Model):
	_inherit = 'stock.move'

	interco_master = fields.Boolean(related="picking_id.interco_master", readonly=True)
	interco_move_line_ids = fields.One2many('stock.interco.move.line', 'move_id', string="Interco Move Line")
	interco_move_line_qty_done = fields.Float(string="Selected", digits='Product Unit of Measure', compute="_compute_interco_move_line")
	interco_src_location_names = fields.Char(compute="_compute_interco_src_location_ids", string="Selected Locations")
	warehouse_plant_id = fields.Many2one(related="picking_id.warehouse_plant_id", readonly=True)
	picking_state = fields.Selection(related='picking_id.state',string='Picking State')

	allowed_company_ids = fields.Many2many('res.company','stock_move_allowed_company_rel', 'stock_move_id', 'res_company_id', compute="_compute_allowed_company_ids", store=True, onupdate="cascade", ondelete="cascade")
	

	to_backorder = fields.Boolean('Backorder', copy=False, default=True)
	desc_product = fields.Text(related='sale_line_id.name', string="Description")
	# desc_product = fields.Text(related='purchase_line_id.name', string="Description")


	@api.depends('picking_id','company_id')
	def _compute_allowed_company_ids(self):
		for rec in self:
			alloweds = rec.company_id
			if rec.picking_id.id:
				alloweds += rec.picking_id.allowed_company_ids
			rec.allowed_company_ids = alloweds.ids

	def read(self, fields=None, load='_classic_read'):
		return super(StockMove, self.sudo()).read(fields=fields, load=load)

	@api.constrains('to_backorder','interco_move_line_ids')
	def _constrains_to_backorder(self):
		for line in self:
			lot_id = False
			for rec in line.interco_move_line_ids:
				if rec.lot_id:
					lot_id = True

			if line.to_backorder and lot_id:
				raise ValidationError(_('If Backorder is Checked, Lot Must Be Empty!'))

	def _compute_interco_src_location_ids(self):
		for rec in self:
			rec.update({
				'interco_src_location_names': ", ".join(rec.interco_move_line_ids.with_user(1).mapped('src_location_id.display_name'))
			})
	
	def _action_cancel(self):
		print("CANELLLLLLLLLLLLLLLLLLLL")
		if any(move.state == 'done' and not move.scrapped for move in self):
			raise UserError(_('You cannot cancel a stock move that has been set to \'Done\'.'))
		moves_to_cancel = self.filtered(lambda m: m.state != 'cancel')
		# self cannot contain moves that are either cancelled or done, therefore we can safely
		# unlink all associated move_line_ids
		moves_to_cancel._do_unreserve()

		for move in moves_to_cancel:
			siblings_states = (move.move_dest_ids.mapped('move_orig_ids') - move).mapped('state')
			if move.propagate_cancel:
				# only cancel the next move if all my siblings are also cancelled
				if all(state == 'cancel' for state in siblings_states):
					move.move_dest_ids.filtered(lambda m: m.state != 'done')._action_cancel()
			else:
				if all(state in ('done', 'cancel') for state in siblings_states):
					move.move_dest_ids.write({'procure_method': 'make_to_stock'})
					move.move_dest_ids.write({'move_orig_ids': [(3, move.id, 0)]})
		self.write({'state': 'cancel', 'move_orig_ids': [(5, 0, 0)]})
		return True

	def write(self,vals):
		if len(self)==1 and not self._context.get('super'):
			interco_user = self.env.company.intercompany_user_id.id
			if interco_user and self.interco_master:
				# fix me
				return super(StockMove, self).with_context(super=True).with_user(interco_user).write(vals)

		return super(StockMove, self).write(vals)

	def _compute_interco_move_line(self):
		for rec in self:
			rec.interco_move_line_qty_done = sum(rec.interco_move_line_ids.mapped('qty'))


	def action_show_details(self):
		
		for rec in self:
			
			if rec.interco_master and rec.picking_id.picking_type_code == 'outgoing':
				if rec.picking_id.warehouse_plant_id.id==False:
					self.env.cr.rollback()
					return {
						'effect': {
							'fadeout': 'slow',
							'message': _("You need to fill Plant First"),
							'img_url': '/sanqua_sale_flow/static/src/img/wow.png',
							'type': 'rainbow_man',
						}
					}
		Env = self.with_user(SUPERUSER_ID).with_context(allowed_company_ids=self.company_id.ids+self.env.user.company_id.ids)
		sup = super(StockMove, Env).action_show_details()
		
		context = sup.get('context')
		companies = self.env['res.company'].with_context(allowed_company_ids=self.company_id.ids+self.env.user.company_id.ids).with_user(SUPERUSER_ID).search([('id','!=',False)])
		
		context.update({
			'default_warehouse_id':self.picking_id.warehouse_plant_id.id,
			'using_intercompany_user':self.env.company.intercompany_user_id.id,
			'allowed_company_ids':self.company_id.ids+self.env.user.company_id.ids,
			})
		sup.update({'context':context})
		return sup


	def btn_select_lots(self):
		return {
				'name':'Interco Move Line',
				'view_mode': 'form',
				'view_ids':[(False, 'form')],
				'res_model':'stock.interco.move.line',
				'type':'ir.actions.act_window',
				'target':'new',
				'context': {
						'default_product_id':self.product_id.id,
						'all_companies':True,
						'tree_view_ref':'sanqua_sale_flow.stock_interco_move_line_editable_tree',
						'default_picking_id':self.picking_id.id,
						'default_move_id':self.id
					}
				}