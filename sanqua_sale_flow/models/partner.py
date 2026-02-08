# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError

import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
	_inherit = 'res.partner'

	can_direct_pickup = fields.Boolean("Direct Pickup", default=False, track_visibility="onchange", help=_("Can Pickup an Order Directly to Plant"))
	direct_pickup_reduction_amount = fields.Monetary(string="Reduction Amount", help="When Customer Picking Up Directly, will reducing cost of deliver order and will be generated as discount on Sales Order")
	allowed_product_category_ids = fields.Many2many('product.category',compute='_compute_allowed_product_category_ids', string='Allowed category')

	payment_method = fields.Selection([('cash', 'Cash'),('transfer', 'Transfer')], string='Payment Method', default='cash')
	collection_method = fields.Selection([('collector', 'Collector'),('admin', 'Admin'), ('salesman','Salesman')], string='Collection Method')

	property_product_pricelist = fields.Many2one(
        'product.pricelist', 'Pricelist', compute=False,
        inverse=False, company_dependent=False, required=False,
        help="This pricelist will be used, instead of the default one, for sales to the current partner")

	def check_partner_pricelist(self, team):
		# check where pricelist is not in partner_pricelist
		if type(team)==int:
			team = self.env['crm.team'].sudo().browse(team)
		if not len(team):
			raise ValidationError(_("Team not defined or not found in database!"))
		no_team_pricelist = self.filtered(lambda r:not any(r.partner_pricelist_ids.mapped(lambda rr:rr.sudo().team_id.id==team.sudo().id)))
		if len(no_team_pricelist):
			raise ValidationError(_("No pricelist for team %s defined for:\n%s ") % (team.sudo().display_name, "\n".join(no_team_pricelist.mapped(lambda r:r.display_name)),))



	def _compute_allowed_product_category_ids(self):
		for rec in self:
			product_category = []
			for team in rec.partner_pricelist_ids.mapped('team_id'):
				product_category += team.product_category_ids.ids
			rec.allowed_product_category_ids = [(6,0,product_category)]


	@api.constrains('team_id','direct_pickup_reduction_amount')
	def constrains_direct_pickup(self):
		not_valid = self.filtered(lambda r:r.can_direct_pickup==True and (r.team_id.id == False or r.direct_pickup_reduction_amount<=0.0))
		if len(not_valid):
			raise ValidationError(_("Is Can Direct Pickup. Please Define Division and Reduction Amount"))

	@api.constrains('team_id')
	def constrains_team_id(self):
		if self.team_id.id:
			self.team_id = self.team_id.id