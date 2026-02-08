# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError

import logging
_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
	_inherit = 'res.company'

	using_interco_master_on_sale = fields.Boolean(string="Default Order as Intercompany Procurement", default=False)


	def name_get(self):
		res = []
		context = self._context
		if context.get('allowed_company_ids'):
			sup = super(ResCompany, self.with_user(1).with_context(dict(allowed_company_ids=context.get('allowed_company_ids')))).name_get()
		elif context.get('all_companies'):
			all_comp = self.env['res.company'].with_user(1).search([('id','!=',False)])
			sup = super(ResCompany, self.with_user(1).with_context(dict(allowed_company_ids=all_comp.ids))).name_get()
		else:
			sup = super(ResCompany, self.with_user(1)).name_get()
		return sup

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		if self._context.get('all_companies'):
			return super(ResCompany, self.with_user(self.env.user.company_id.intercompany_user_id.id)).name_search(name=name, args=args, operator=operator, limit=limit)
		return super(ResCompany, self.with_user(1)).name_search(name=name, args=args, operator=operator, limit=limit)