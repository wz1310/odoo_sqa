from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class StockMoveLine(models.Model):
	_inherit = 'stock.move.line'

	allowed_company_ids = fields.Many2many('res.company','stock_move_line_allowed_company_rel', 'stock_move_line_id', 'res_company_id', compute="_compute_allowed_company_ids", store=True, onupdate="cascade", ondelete="cascade")
	available_lot_in_location = fields.Many2many('stock.production.lot', compute="_check_available_lot", string="Available Lot")
	free_qty = fields.Float('Free To Use Quantity', digits='Product Unit of Measure')

	# lot_id = fields.Many2one(
	#     'stock.production.lot', 'Lot/Serial Number',
	#     domain="[('product_id', '=', product_id), ('company_id', '=', company_id)]", check_company=True)
	# , ('product_qty_from_lot_id', '>', 0.0)
	@api.depends('location_id','move_id')
	def _check_available_lot(self):
		"""Internal transfer, DO, GR, Return GR : available lot > available qty > 0
			Return DO : same lot with DO
		"""
		Lot = self.env['stock.production.lot']
		result_lot = []
		for rec in self.sudo():
			AvailableLot = self.env['stock.production.lot']
			AvailableLotGR = self.env['stock.production.lot']
			AvailableLotDoReturn = self.env['stock.production.lot']

			quant_ids = self.env['stock.quant'].search([('product_id', '=', rec.product_id.id),
														('location_id', '=', rec.location_id.id)])
			for quant in quant_ids:
				AvailableLotGR += quant.lot_id
				available = quant.quantity
				if available > 0.0:
					AvailableLot += quant.lot_id

			print('>>> rec.picking_id : ' + str(rec.picking_id))
			print('>>> rec.picking_id.origin_returned_picking_id : ' + str(rec.picking_id.origin_returned_picking_id))

			if rec.picking_id.origin_returned_picking_id:
				print('>>> Here 1...')
				for move in rec.picking_id.origin_returned_picking_id.move_ids_without_package:

					# Edited by : MIS@SanQua
					# At: 10/01/2022
					# Description : take out validation 'and move.product_uom_qty == rec.move_id.product_uom_qty:' to show all lot based on DO origin
					if move.move_line_nosuggest_ids and move.product_id.id == rec.move_id.product_id.id:
						print('>>> Here 2...')
						for line in move.move_line_nosuggest_ids:
							AvailableLotDoReturn += line.lot_id
				print('# Back Order ID : ' + str(rec.picking_id.backorder_id))
				if rec.picking_id.backorder_id and rec.picking_id.backorder_id.origin_returned_picking_id == rec.picking_id.origin_returned_picking_id:
					print('>>> Here 3...')
					for move in rec.picking_id.origin_returned_picking_id.move_ids_without_package:
						if move.move_line_nosuggest_ids and move.product_id.id == rec.move_id.product_id.id:
							print('>>> Here 4...')
							for line in move.move_line_nosuggest_ids:
								AvailableLotDoReturn += line.lot_id
			if rec.move_id.picking_type_id.code == 'internal':
				result_lot = [(6,None, AvailableLot.ids)]
			elif rec.move_id.picking_type_id.code in ('outgoing' , 'incoming'):
				print('>>> Here 5...')
				result_lot = [(6,None, AvailableLot.ids)]
				if rec.move_id.picking_type_id.code == 'outgoing' and rec.picking_id.origin_returned_picking_id:
					print('>>> Here 6...')
					result_lot = [(6,None, AvailableLot.ids)]
				if rec.move_id.picking_type_id.code == 'incoming' and rec.picking_id.origin_returned_picking_id:
					print('>>> Here 7...')
					result_lot = [(6,None, AvailableLotDoReturn.ids)]
			else:
				result_lot = [(6,None, AvailableLot.ids)]

			rec.update({
					'available_lot_in_location': result_lot
			})
			

	@api.depends('company_id','move_id')
	def _compute_allowed_company_ids(self):
		for rec in self:
			alloweds = rec.company_id
			if rec.move_id.id:
				alloweds += rec.move_id.allowed_company_ids
			rec.allowed_company_ids = alloweds.ids

	def read(self, fields=None, load='_classic_read'):
		return super(StockMoveLine, self.sudo()).read(fields=fields, load=load)

	def _get_lot_free_qty(self):
		self.ensure_one()
		context = self._context.copy()
		context.update({'allowed_company_ids':self.allowed_company_ids.ids, 'lot_id':self.lot_id.id})
		quant = self.with_context(context).\
				env['stock.quant'].search([('product_id', '=', self.product_id.id),
											('location_id', '=', self.location_id.id),
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