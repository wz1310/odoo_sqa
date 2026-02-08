# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
	_inherit = 'sale.order'
	
	interco_company_id = fields.Many2one('res.company', string="Interco Company", ondelete="restrict", onupdate="restrict")
	interco_purchase_id = fields.Many2one('purchase.order', string="Interco Purchase", ondelete="restrict", onupdate="restrict", copy=False)
	interco_purchase_ids = fields.Many2many('purchase.order', 'interco_purchase_order_sale_order_rel', 'interco_purchase_id', 'interco_sale_id', string='Interco Purchases',copy=False)

	def can_create_new_interco_po(self):
		self.ensure_one()
		# can create if interco_purchase_id is None or interco_purchase_id.state == 'cancel'
		res = True if not self.interco_purchase_id.id or self.interco_purchase_id.state=='cancel' else False
		if res:
			res = True if self.interco_company_id.id else False
		return res


	def validating_interco_po(self):
		raise ValidationError(_("Interco Company Can't same as Company on Sale Order Document!")) if self.interco_company_id.id == self.company_id.id else None



	def _prepare_interco_purchase_line(self, purchase, so_line):
		self.ensure_one()

		def apply_onchange(new_obj, skips = []):
			for field_name,mthds in new_obj._onchange_methods.items():
				if field_name not in skips:
					new_obj._onchange_eval(field_name,'1',{})
			return new_obj

		# prepare object first
		data = {
			'order_id':purchase.id,
			'product_id':so_line.product_id.id,
		}
		new_obj = self.env['purchase.order.line'].new(data)
		
		new_obj = apply_onchange(new_obj,'') # apply onchange --> all method
		new_obj.update({'name':so_line.name})
		picking_id = self.env['stock.picking'].browse(self._context.get('picking_id'))
		picking_line_id = self.env['stock.move'].search([('picking_id','=',picking_id.id),('sale_line_id','=',so_line.id),('product_id','=',so_line.sudo().product_id.id)])

		datas = []
		for line in picking_line_id:
			if line.interco_move_line_qty_done > 0:
				new_obj.update({
					'product_uom_qty':line.interco_move_line_qty_done,
					'product_qty':line.interco_move_line_qty_done,
					'price_unit':self.env['inter.company.pricelist'].get_product_fixed_price(self.plant_id,purchase.company_id.partner_id,so_line.product_id),
					})
				new_obj = apply_onchange(new_obj.sudo(), ['product_id','product_uom_qty', 'product_qty','product_uom']) #apply onchange without onchange product_id
				to_write = new_obj._convert_to_write({name: new_obj[name] for name in new_obj._cache})
				datas.append(to_write)
		return datas
		


	def _prepare_interco_purchase(self):
		res = {}
		picking_id = self.env.context.get('picking_id')
		validity_date = self.env.context.get('validity_date')
		new_order_data = {
			'partner_id':self.sudo().interco_company_id.partner_id.id,
			'partner_ref':self.name,
			'date_order':fields.Datetime.now(),
			'company_id':self.sudo().company_id.id,
			'user_id':self.sudo().company_id.intercompany_user_id.id,
			'interco_picking_id':picking_id,
			}

		new_order = self.env['purchase.order'].sudo().new(new_order_data)
		
		onchange_res = {}
		for field_name,mthds in new_order._onchange_methods.items():
			new_order._onchange_eval(field_name,'1',onchange_res)
		lines = []
		res = new_order._convert_to_write({name: new_order[name] for name in new_order._cache})
		for line in self.sudo().order_line:
			datas = self._prepare_interco_purchase_line(new_order, line)
			for data in datas:
				lines.append((0,0,data))

		res.update({
			'order_line':lines
			})


		return res

	def create_interco_purchase_order(self):
		self.ensure_one()
		
		# if not self.can_create_new_interco_po():
		# 	raise UserError(_("Only can creating PO wich condition:\n \n - Interco Company Defined \n- No Existing created PO OR created PO must be on CANCELLED!"))
		new_purchase_data = self._prepare_interco_purchase()
		
		po = self.env['purchase.order'].with_user(self.company_id.intercompany_user_id).sudo().create(new_purchase_data)
		self.interco_purchase_ids = [(4, po.id)]
		if len(po) == 1:
			# assert len(po.order_line)==len(self.sudo().order_line), _("Created PO Lines not Matched with Order Line. Please Contact System Administrator")
			
			query = "UPDATE sale_order SET interco_purchase_id	= %s WHERE id IN %s"
			
			params = (po.id, tuple(self.ids))
			
			self.env.cr.execute(query, params)
			self.invalidate_cache()
			
			# po.with_context(force_request=1, foce_company=self.company_id.intercompany_user_id.id).button_approve()
			po.with_context(force_request=1).button_approve()
			# self.create_invoice(po)
			return True
		else:
			raise ValidationError(_("Failed to create Interco PO"))


	def create_invoice(self,po):
		invoice_vals = {
			'type': 'in_invoice',
			'invoice_origin': po.name,
			'invoice_user_id': po.user_id.id,
			'partner_id': po.partner_id.id,
			'team_id': po.interco_sale_id.team_id.id,
			'purchase_id': po.id,
			'ref':po.display_name,
			'company_id': po.company_id.id,
			'invoice_line_ids':[]
		}
		for rec in po.order_line.filtered(lambda r:r.qty_received>0.0):
			invoice_vals['invoice_line_ids'].append(
					(0, 0, {
						'name': rec.name,
						'price_unit': rec.price_unit,
						'quantity': rec.qty_received,
						'product_id': rec.product_id.id,
						'product_uom_id': rec.product_uom.id,
						'tax_ids': [(6, 0, rec.taxes_id.ids)],
						'purchase_line_id': rec.id,
						'multi_discounts' : rec.multi_discounts,
						'discount_fixed_line' : rec.discount_fixed_line,
						'discount' : rec.discount,
						'analytic_tag_ids': [(6, 0, rec.analytic_tag_ids.ids)],
						'analytic_account_id': rec.account_analytic_id.id or False,
					})
				)
		invoice_id = self.env['account.move'].create(invoice_vals)