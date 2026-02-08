# -*- coding: utf-8 -*-
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import UserError,ValidationError

import logging
_logger = logging.getLogger(__name__)


class StockProductionLot(models.Model):
	_inherit = 'stock.production.lot'

	product_qty_from_lot_id = fields.Float('Quantity', compute='_product_qty_lot', store=True)

	@api.depends('quant_ids', 'quant_ids.location_id.usage', 'quant_ids.quantity')
	def _product_qty_lot(self):
		for lot in self:
			quants = lot.quant_ids.filtered(lambda q: q.location_id.usage in ['internal', 'transit'])
			lot.product_qty_from_lot_id = sum(quants.mapped('quantity'))

	def read(self, fields=None, load='_classic_read'):
		return super(StockProductionLot, self.sudo()).read(fields=fields, load=load)

	def name_get(self):
		
		if self._context.get('force_company'):
			context = self._context.copy()
			context.update({'allowed_company_ids':[self._context.get('force_company')]})
			self = self.with_context(context).sudo()
		
		res = super(StockProductionLot, self).name_get()
		return res

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		if self._context.get('force_company'):
			context = self._context.copy()
			context.update({'allowed_company_ids':[self._context.get('force_company')]})
			self = self.with_context(context).sudo()
		return super(StockProductionLot, self).name_search(name=name, args=args, operator=operator, limit=limit)

	@api.model
	def fetch_company_lot(self, lot, company):
		self = self.with_user(SUPERUSER_ID)
		lot = lot.with_user(SUPERUSER_ID)
		# find lot in company
		# if found return it
		# if not create it
		Lot = self.search([('name','=',lot.name), ('product_id','=',lot.product_id.id), ('company_id','=',company.id)])
		if len(Lot):
			return Lot
		else:
			return self._copy_lot(lot, company)


	@api.model
	def _copy_lot(self, lot, company):
		lot = lot.with_user(SUPERUSER_ID)
		company = company.with_user(SUPERUSER_ID)
		return self.with_user(SUPERUSER_ID).create(dict(
			name=lot.name, ref=lot.name, product_id=lot.product_id.id, company_id=company.id))