# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError

import logging
_logger = logging.getLogger(__name__)


class SaleAgreement(models.Model):
	_inherit = 'sale.agreement'
	
	partner_id = fields.Many2one('res.partner', string="Customer", required=True, domain=[('is_company','=',True),('customer','=',True),('state','=','approved')])

	"""Create So from sale agreement
	@override from sale_agreement
	"""
	def create_so_from_sale_agreement(self):
		sup = super().create_so_from_sale_agreement()
		if self.env.company.using_interco_master_on_sale:
			self.env.cr.execute("UPDATE sale_order SET interco_master = true WHERE id in (SELECT id FROM sale_order AS so WHERE so.sale_agreement_id=%s  AND so.state = 'draft' ORDER BY so.id DESC LIMIT 1)", (self.id,))
		return sup

	def name_get(self):
		res = []
		for rec in self:
			name = "%s | %s | %s | %s" % (rec.name, rec.team_id.display_name, rec.start_date.strftime('%d/%m/%Y'), sum(rec.agreement_line_ids.mapped('product_qty')), )
			res += [(rec.id, name)]
		return res
	

	def display_name(self):
		super().display_name()
		for rec in self:
			rec.display_name = "%s | %s | %s | %s" % (rec.name, rec.team_id.display_name, rec.start_date.strftime('%d/%m/%Y'), sum(rec.agreement_line_ids.mapped('product_qty')), )