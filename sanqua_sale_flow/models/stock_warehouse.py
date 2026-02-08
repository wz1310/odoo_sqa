# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError

import logging
_logger = logging.getLogger(__name__)


class StockWarehouse(models.Model):
	_inherit = 'stock.warehouse'

	other_wh_can_read = fields.Boolean(default=False)

	def read(self, fields=None, load='_classic_read'):
		return super(StockWarehouse, self).read(fields=fields, load=load)

	def name_get(self):
		res = []
		context = self._context
		if context.get('allowed_company_ids'):
			sup = super(StockWarehouse, self.with_context(dict(allowed_company_ids=(self.env.company.ids+context.get('allowed_company_ids'))))).name_get()
		elif context.get('all_companies'):
			
			all_comp = self.env['res.company'].with_user(1).search([('id','!=',False)])
			sup = super(StockWarehouse, self.with_context(dict(allowed_company_ids=all_comp.ids)).sudo()).name_get()
		else:
			sup = super(StockWarehouse, self.sudo()).name_get()
		return sup

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		# args = args or []
		# connector = '|'
		# recs = self.search([connector, ('code', operator, name), ('name',operator,name)] + args, limit=limit)
		# return recs.name_get()
		
		domain_company_id = self._context.get('domain_company_id')
		if domain_company_id:
			for arg in args:
				if arg[0]=='company_id':
					arg[2] = domain_company_id
			new_context = self._context.copy()
			del new_context['domain_company_id']
			return super(StockWarehouse, self).with_context(new_context).with_user(self.env.user.company_id.intercompany_user_id.id).name_search(name=name, args=args, operator=operator, limit=limit)

		elif self._context.get('all_companies'):
			return super(StockWarehouse, self.with_user(self.env.user.company_id.intercompany_user_id.id)).name_search(name=name, args=args, operator=operator, limit=limit)
		return super(StockWarehouse, self).name_search(name=name, args=args, operator=operator, limit=limit)
