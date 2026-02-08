"""File sale order truck"""
from odoo import api, fields, models, _

class SaleOrder(models.Model):
	_inherit = "sale.order"

	
	sale_truck_id = fields.Many2one('sale.order.truck', string="sale Truck", track_visibility='onchange')
	sale_truck_mix_ids = fields.Many2many('sale.order.truck', 'sale_id','sale_truck_id', 'sale_order_sale_truck_rel', string='Sale Truck Mix Ref.',track_visibility='onchange')

	def _prepare_interco_purchase_line_truck(self, purchase, so_line):
		print("_prepare_interco_purchase_line_truck")
		self.ensure_one()

		def apply_onchange(new_obj, skips = []):
			print("apply_onchange")
			for field_name,mthds in new_obj._onchange_methods.items():
				if field_name not in skips:
					new_obj._onchange_eval(field_name,'1',{})
			return new_obj        

		data = {
			
			'product_id':so_line.product_id.id,
		}
		new_obj = self.env['purchase.order.line'].new(data)
		
		new_obj = apply_onchange(new_obj) # apply onchange --> all method
		# picking_id = self.sudo().sale_truck_id.transit_out
		# picking_line_id = self.env['stock.move'].search([('picking_id','=',picking_id.id),('sale_line_id','=',so_line.id),('product_id','=',so_line.sudo().product_id.id)])

		datas = []
		new_obj.update({
			'product_uom_qty':so_line.product_uom_qty,
			'product_qty':so_line.product_uom_qty,
			'name':so_line.name
			})
		new_obj = apply_onchange(new_obj.sudo(), ['product_id']) #apply onchange without onchange product_id
		new_obj._onchange_quantity()

		to_write = new_obj._convert_to_write({name: new_obj[name] for name in new_obj._cache})
		# datas.append(to_write)
		return to_write

	def _prepare_interco_purchase(self):
		print("_prepare_interco_purchase")
		res = super()._prepare_interco_purchase()

		new_order_data = {
			'partner_id':self.sudo().interco_company_id.partner_id.id,
			'partner_ref':self.name,
			'date_order':fields.Datetime.now(),
			'company_id':self.sudo().company_id.id,
			'user_id':self.sudo().company_id.intercompany_user_id.id,
			}

		new_order = self.env['purchase.order'].sudo().new(new_order_data)
		
		onchange_res = {}
		for field_name,mthds in new_order._onchange_methods.items():
			new_order._onchange_eval(field_name,'1',onchange_res)
		lines = []
		tmp_po = new_order._convert_to_write({name: new_order[name] for name in new_order._cache})


		if self.sale_truck_id.id:
			pols = []
			for line in self.sudo().order_line:
				# res.update({'order_line':})
				pols.append([0,0,self._prepare_interco_purchase_line_truck(new_order, line)])

			res.update({'order_line':pols})
		return res


class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'

	def _action_launch_stock_rule(self, previous_product_uom_qty=False):
		if self._context.get('disable_launch_stock_rule') and all(self.mapped(lambda r:r.order_id.sale_truck_id.id)):
			return True
		return super()._action_launch_stock_rule(previous_product_uom_qty=previous_product_uom_qty)