import datetime
from odoo import fields,api,models,_
from odoo.exceptions import UserError
from datetime import datetime
import odoo.addons.decimal_precision as dp

class MrpProduction(models.Model):
	_inherit = 'mrp.production'

	mesin_id = fields.Many2one('mrp.mesin')
	kapasitas = fields.Float(string='Kapasitas')
	satuan_id = fields.Many2one('uom.uom', string='Satuan')
	history_line = fields.One2many('mrp.production.history.mesin', 'production_id', string='Information')
	group_id = fields.Many2one('mrp.production.group','Group')
	jml_personel = fields.Integer('Total Personel')
	# total_jam_kerja = fields.Integer('Total Working Hours')
	total_jam_kerja = fields.Float('Total Working Hours')
	qty_produced = fields.Float(compute="_get_produced_qty", string="Quantity Produced", store=True)
	produktivitas_mesin = fields.Float(compute="_get_productivitas_machine", string="Produktivitas Mesin", store=True)
	kwh_mesin = fields.Float(string='Kwh / Jam')
	target_produksi = fields.Float(string='Target Produksi')
	mesin_line_id = fields.Many2one('mrp.mesin.information', string="Line Mesin")
	consumption = fields.Float('Consumption', compute="_get_productivitas_machine", store=True)
	bom_amount = fields.Float('BoM Amount (Rp)', store=True, compute='_compute_reject_produksi_qty')
	produksi_amount = fields.Float('FG Amount (Rp)', store=True, compute='_compute_reject_produksi_qty')
	reject_produksi_persen = fields.Float('Reject Production (%)', store=True, compute='_compute_reject_produksi_qty')
	reject_produksi_amount = fields.Float('Reject Amount (Rp)', store=True, compute='_compute_reject_produksi_qty')
	reject_produksi_qty = fields.Float('Reject Qty', store=True, compute='_compute_reject_produksi_qty')

	@api.depends('state')
	def _compute_reject_produksi_qty(self):
		for data in self:
			bom_amount = 0.0
			produksi_amount = 0.0
			reject_produksi_amount = 0.0
			reject_produksi_qty = 0.0
			if data.bom_id:
				for row in data.move_raw_ids:
					if row.raw_material_production_id and row.state in ('done','waiting_qc','qc_done') and row.product_uom_qty > 0 and row.quantity_done > 0:
						price_un = row.product_id.with_context(force_company=data.company_id.id).standard_price
						if row.reference == 'New':
							row.reject_produksi_qty = row.quantity_done
							row.bom_amount = 0.0
						else:
							row.reject_produksi_qty = row.quantity_done - row.product_uom_qty
							row.bom_amount = row.product_uom_qty * price_un
						
						reject_produksi_qty += row.reject_produksi_qty
						row.reject_produksi_persen = (row.reject_produksi_qty / row.product_uom_qty) * 100
						row.reject_produksi_amount = row.reject_produksi_qty * price_un
						row.produksi_amount = row.quantity_done * price_un
						bom_amount += row.bom_amount
						produksi_amount += row.produksi_amount
						reject_produksi_amount += row.reject_produksi_amount
				
					data.bom_amount = bom_amount
					data.produksi_amount = produksi_amount
					data.reject_produksi_amount = reject_produksi_amount
					data.reject_produksi_qty = reject_produksi_qty
					if bom_amount > 0 and produksi_amount > 0 and reject_produksi_amount > 0:
						data.reject_produksi_persen = (reject_produksi_amount / bom_amount) * 100

	def _update_init(self):
		for data in self.search([]):
			bom_amount = 0.0
			produksi_amount = 0.0
			reject_produksi_amount = 0.0
			reject_produksi_qty = 0.0
			if data.bom_id and data.state in ('done','waiting_qc','qc_done'):
				for row in data.move_raw_ids:
					if row.raw_material_production_id and row.product_uom_qty > 0 and row.quantity_done > 0:
						price_un = row.product_id.with_context(force_company=data.company_id.id).standard_price

						if row.reference == 'New':
							row.reject_produksi_qty = row.quantity_done
							row.bom_amount = 0.0
						else:
							row.reject_produksi_qty = row.quantity_done - row.product_uom_qty
							row.bom_amount = row.product_uom_qty * price_un
						
						reject_produksi_qty += row.reject_produksi_qty
						row.reject_produksi_persen = (row.reject_produksi_qty / row.product_uom_qty) * 100
						row.reject_produksi_amount = row.reject_produksi_qty * price_un
						row.produksi_amount = row.quantity_done * price_un
						bom_amount += row.bom_amount
						produksi_amount += row.produksi_amount
						reject_produksi_amount += row.reject_produksi_amount
					data.bom_amount = bom_amount
					data.produksi_amount = produksi_amount
					data.reject_produksi_amount = reject_produksi_amount
					data.reject_produksi_qty = reject_produksi_qty
					if bom_amount > 0 and produksi_amount > 0 and reject_produksi_amount > 0:
						data.reject_produksi_persen = (reject_produksi_amount / bom_amount) * 100
						
	@api.depends('workorder_ids.state', 'move_finished_ids', 'move_finished_ids.quantity_done', 'is_locked')
	def _get_produced_qty(self):
		for production in self:
			done_moves = production.move_finished_ids.filtered(lambda x: x.state != 'cancel' and x.product_id.id == production.product_id.id)
			qty_produced = sum(done_moves.mapped('quantity_done'))
			production.qty_produced = qty_produced
		return True

	@api.depends('state', 'move_finished_ids', 'move_finished_ids.quantity_done', 'kapasitas', 'kwh_mesin','total_jam_kerja')
	def _get_productivitas_machine(self):
		for production in self:
			production._calculate_target()
			produktivitas_mesin = 0.0
			consumption = 0.0
			if production.move_finished_ids:
				if production.qty_produced and production.kapasitas and production.target_produksi > 0:
					produktivitas_mesin = production.qty_produced / production.target_produksi * 100
				if production.kwh_mesin and production.total_jam_kerja and production.qty_produced:
					consumption = production.total_jam_kerja * production.kwh_mesin
			production.produktivitas_mesin = produktivitas_mesin
			production.consumption = consumption

	def update_init(self):
		for reza in self.search([]):
			if reza.mesin_id:
				information_mesin = reza.env['mrp.mesin.information'].search([('mesin_id','=',reza.mesin_id.id),('company_id','=',reza.company_id.id),('sku_id','=', reza.product_id.id)])
				if information_mesin:
					reza.kapasitas = information_mesin.kapasitas
					reza.satuan_id = information_mesin.satuan_id
					reza.kwh_mesin = reza.mesin_id.kwh_per_jam
					reza.target_produksi = information_mesin.target_prod * reza.total_jam_kerja
					reza.mesin_line_id = information_mesin
			reza._get_productivitas_machine()
	
	def _calculate_target(self):
		for prod in self:
			if prod.mesin_id:
				information_mesin = prod.env['mrp.mesin.information'].search([('mesin_id','=',prod.mesin_id.id),('company_id','=',prod.company_id.id),('sku_id','=', prod.product_id.id)])
				if information_mesin:
					prod.target_produksi = information_mesin.target_prod * prod.total_jam_kerja
					
	@api.onchange('mesin_id')
	def _onchange_mesin_id(self):
		for prod in self:
			if prod.mesin_id:
				information_mesin = prod.env['mrp.mesin.information'].search([('mesin_id','=',prod.mesin_id.id),('company_id','=',prod.company_id.id),('sku_id','=', prod.product_id.id)])
				if information_mesin:
					prod.kapasitas = information_mesin.kapasitas
					prod.satuan_id = information_mesin.satuan_id
					prod.kwh_mesin = prod.mesin_id.kwh_per_jam
					prod.target_produksi = information_mesin.target_prod * prod.total_jam_kerja
					prod.mesin_line_id = information_mesin
				else:
					raise UserError(_('Not found for information plant %s and SKU %s' %(prod.company_id.name, prod.product_id.name)))


	def button_mark_done(self):
		#Change Date
		name_lot = self.code_production
		self.onchange_date_mo()
		code = self.create_lot_number_production()
		#raise UserError(_(('%s -- %s') % (name_lot, code)))
		if name_lot != code:
			lot = self.env['stock.production.lot']
			dt_lot = lot.search([('name', '=', name_lot),('product_id','=',self.product_id.id)])
			dt_lot.name = code
			
			self.code_production = code

		for raw in self.move_raw_ids:
			prod_ids = self.move_raw_ids.filtered(lambda x: x.product_id.id == raw.product_id.id)
			sum_to_consume = sum(prod_ids.mapped('product_uom_qty'))
			sum_done = sum(prod_ids.mapped('quantity_done'))
			if sum_to_consume > sum_done:
				raise UserError(_("Qty Consume tidak boleh lebih kecil dari Qty To Consume (BoM)\nProduct : %s\nTo Consume : %s \nConsume : %s" % (raw.product_id.name,sum_to_consume,sum_done)))
			quant = 0.0
			for move in raw.move_line_ids:
				if move.lot_id.id:
					quant = self.env['stock.quant'].search([('product_id', '=', raw.product_id.id),
													('location_id', '=', self.location_src_id.id),
													('lot_id', '=', move.lot_id.id)])
				else:
					quant = self.env['stock.quant'].search([('product_id', '=', raw.product_id.id),
												('location_id', '=', self.location_src_id.id)])
				
				stock = quant.quantity
				# if move.qty_to_consume > 0:
				# 	# if raw.qty_to_consume > raw.qty_done:
				# 	#     raise UserError(_("Kata Pak Mardi Haram lebih kecil"))
				# 	stock = quant.quantity
				# elif move.qty_to_consume == 0:
				# 	stock = quant.quantity - quant.reserved_quantity

				if move.qty_done > stock:
					raise UserError(_("Stock untuk Product %s \nLot : %s \nkurang dari yang dibutuhkan, Mohon periksa ketersediaan stock di %s\nStock Tersedia : %s\nDibutuhkan : %s\nKurang : %s") % (raw.product_id.name,move.lot_id.name,self.location_src_id.display_name,stock,move.qty_done,stock-move.qty_done))

		res = super(MrpProduction, self).button_mark_done()
		vals_history = {
			'mesin_id': self.mesin_id.id,
			'date': datetime.today(),
			'user_id': self.user_id.id,
			'production_id': self.id,
			'history': '-',
		}
		self.env['mrp.mesin.history'].create(vals_history)
		return res

class MrpProductionHistoryMesin(models.Model):
	_name = 'mrp.production.history.mesin'

	production_id = fields.Many2one('mrp.production')
	type_mesin_information = fields.Selection([('downtime','Downtime'),('breakdown','Breakdown')], string='Mesin Information')
	timestart = fields.Datetime(string='From')
	timeend = fields.Datetime(string='Until')
	reason_id = fields.Many2one('reason', string='Reason')
	notes = fields.Char(string='Notes')
	duration = fields.Float(string='Duration')
