# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError,ValidationError

from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

import xml.etree as etr
import xml.etree.ElementTree as ET
from ast import literal_eval

class SaleCouponProgram(models.Model):
	_inherit = 'sale.coupon.program'


	rule_sale_domain = fields.Char(string="Sale Order Domain", help="Coupon program will work for Selected Sales only")
	state = fields.Selection([('draft','Draft'), ('done','Locked')], default="draft", required=True, string="State", track_visibility="onchange")

	
	free_product_method = fields.Selection([
		('base', 'Base'),
		('extended', 'Extended')
	], string='Free Product Method',default='extended',required=True)
	free_product_selection = fields.Selection([
		('same_on_line', 'Same On Line'),
		('custom', 'Custom')
	], string='Product Rule')
	fix_amount_method = fields.Selection([
		('amount_total', 'Amount Total'),
		('amount_per_unit', 'Amount Per Unit')
	], string='Fix Amount Method')


	def toggle_active(self):
		for rec in self:
			if rec.active == True:
				res = False
			else:
				res = True
			rec.update({'active':res})


	def __authorized_form(self, root):
		def append_nocreate_options(elm):
			# _logger.info(('---- loop', elm.tag,elm.attrib.get('name')))
			
			fields_name = elm.attrib.get('name')

			Many2one = isinstance(self._fields[fields_name], fields.Many2one)
			Many2many = isinstance(self._fields[fields_name], fields.Many2many)
			# One2many = isinstance(self._fields[fields_name], fields.One2many)
			if elm.tag!='field':
				return elm
			
			fields_name = elm.attrib.get('name')

			Many2one = isinstance(self._fields[fields_name], fields.Many2one)
			Many2many = isinstance(self._fields[fields_name], fields.Many2many)
			if elm.tag!='field':
				return elm
			options = elm.get('options')
			if options:
				if (Many2one or Many2many):
					# IF HAS EXISTING "attrs" ATTRIBUTE
					options_dict = literal_eval(options)
					options_nocreate = options_dict.get('no_create')
				
					# if had existing readonly rules on attrs will append it with or operator
					options_dict.update({"no_create":1})
			else:
				if (Many2one or Many2many):
					options_dict = {"no_create":1}
					
			try:
				new_options_str = str(options_dict)
				elm.set('options',new_options_str)
				
			except Exception as e:
				pass
			return elm
		
		def set_nocreate_on_fields(elms):
			for elm in elms:
				if elm.tag=='field':
					elm = append_nocreate_options(elm)
				else:
					if len(elm)>0:
						_logger.info((len(elm)))
						# if elm.tag in ['tree','kanban','form','calendar']:
						# 	continue # skip if *2many field child element
						elm = set_nocreate_on_fields(elm)
					else:
						if elm.tag=='field':
							elm = append_nocreate_options(elm)
			return elms

		def append_readonly(elm):
			if elm.tag!='field':
				return elm

			attrs = elm.get('attrs')
			if attrs:
				# IF HAS EXISTING "attrs" ATTRIBUTE
				attrs_dict = literal_eval(attrs)
				attrs_readonly = attrs_dict.get('readonly')
				# if had existing readonly rules on attrs will append it with or operator
				if attrs_readonly:
					if type(attrs_readonly) == list:
						# readonly if limit_approval_state not in draft,approved
						# incase:
						# when so.state locked (if limit automatically approved the limit_approval_state will still in draft) so will use original functions
						# when so.state == draft and limit approval strate in (need_approval_request,  need_approval, reject) will lock the field form to readonly
						attrs_readonly.insert(0,('state','not in',['draft']))
						attrs_readonly.insert(0,'|')
					attrs_dict.update({'readonly':attrs_readonly})
				else:
					# if not exsit append new readonly key on attrs
					attrs_dict.update({'readonly':[('state','not in',['draft'])]})
			else:
				attrs_dict = {'readonly':[('state','not in',['draft'])]}
			try:
				new_attrs_str = str(attrs_dict)
				elm.set('attrs',new_attrs_str)
			except Exception as e:
				pass

			return elm


		def set_readonly_on_fields(elms):
			for elm in elms:
				if len(elm)>0:
					_logger.info("has %s child(s)" % (len(elm)))
					if elm.tag in ['tree','kanban','form','calendar']:
						continue # skip if *2many field child element
					elm = set_readonly_on_fields(elm)
				else:
					if elm.tag=='field':
						# elm = append_readonly(elm)
						
						# elm.set('readonly','True')
						elm = append_readonly(elm)
			return elms

		
		# form = root.find('form')
		paths = []
		for child in root:
			
			if child.tag=='sheet':
				# child = append_readonly(child)
				
				child = set_readonly_on_fields(child)
				child = set_nocreate_on_fields(child)
		return root

	@api.model
	def _fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
		sup = super()._fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
		# if form
		if view_type=='form':
			root_elm = ET.fromstring("%s" % (sup['arch']), parser=ET.XMLParser(encoding='utf-8'))
			# AUTHORIZED ALL "<field>" element
			new_view = self.__authorized_form(root_elm)
			sup.update({'arch':ET.tostring(new_view)})

		return sup

	@api.onchange('free_product_method')
	def _onchange_(self):
		if self.free_product_method == 'base':
			self.free_product_selection = False
	
	def _is_valid_order(self, order):
		if self.rule_sale_domain:
			domain = safe_eval(self.rule_sale_domain) + [('id', '=', order.id)]
			return bool(self.env['sale.order'].search_count(domain))
		else:
			return True

	def _filter_state(self):
		return self.filtered(lambda r:r.state=='done' and r.active==True)

	# OVERRIDE METHOD FROM odoo.addons.sale_coupon.models.sale_coupon_program
	@api.model
	def _filter_programs_from_common_rules(self, order, next_order=False):
		res = super()._filter_programs_from_common_rules(order=order, next_order=next_order)
		res = res._filter_programs_on_sale(order)
		res._filter_state()
		return res
	
	def _filter_programs_on_sale(self, order):
		return self.filtered(lambda program: program._is_valid_order(order))._filter_state()


	def _filter_not_ordered_reward_programs(self, order):
		"""
		Returns the programs when the reward is actually in the order lines
		"""
		programs = self.env['sale.coupon.program']
		for program in self:
			if program.reward_type == 'discount' and program.discount_apply_on == 'specific_products' and \
			   not order.order_line.filtered(lambda line: line.product_id in program.discount_specific_product_ids):
				continue
			programs |= program
		return programs._filter_state()

	def _check_promo_code(self, order, coupon_code):
		if self.promo_applicability == 'on_current_order' and self.reward_type == 'product' and not order._is_reward_in_order_lines(self):
			return {}
		else:
			return super()._check_promo_code(order, coupon_code)

	def _filter_programs_on_products(self, order):
		"""
		To get valid programs according to product list.
		i.e Buy 1 imac + get 1 ipad mini free then check 1 imac is on cart or not
		or  Buy 1 coke + get 1 coke free then check 2 cokes are on cart or not
		"""
		order_lines = order.order_line.filtered(lambda line: line.product_id) - order._get_reward_lines()
		products = order_lines.mapped('product_id')
		products_qties = dict.fromkeys(products, 0)
		for line in order_lines:
			products_qties[line.product_id] += line.product_uom_qty
		valid_programs = self.filtered(lambda program: not program.rule_products_domain)
		for program in self - valid_programs:
			valid_products = program._get_valid_products(products)
			ordered_rule_products_qty = sum(products_qties[product] for product in valid_products)
			# Avoid program if 1 ordered foo on a program '1 foo, 1 free foo'
			if ordered_rule_products_qty >= program.rule_min_quantity:
				valid_programs |= program
		return valid_programs._filter_state()
