# -*- coding: utf-8 -*-

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged
# from odoo.addons.sale.tests.test_sale_order import TestSaleOrder

import logging
_logger = logging.getLogger(__name__)

# @tagged('-standard', 'nice')
@tagged('post_install', 'at_install')
class TestIntercompanyProcurementOrder(TransactionCase):

	def setUp(self):
		super(TestIntercompanyProcurementOrder, self).setUp()

		SaleOrder = self.env['sale.order'].with_context(tracking_disable=True)
		Partner = self.env['res.partner'].with_context(tracking_disable=True)
		User = self.env['res.users'].with_context(tracking_disable=True)
		ProductTemplate = self.env['product.template'].with_context(tracking_disable=True)
		ProductCategory = self.env['product.category'].with_context(tracking_disable=True)
		CrmTeam = self.env['crm.team'].with_context(tracking_disable=True)

		_logger.debug("Creating company 1")
		self.Company1 = self.env['res.company'].create([{
			'name': "Company1",
		}])
		_logger.debug("Company 1 Created %s" % self.Company1)

		_logger.debug("Creating company 2")
		self.Company2 = self.env['res.company'].create([{
			'name': "Company2",
		}])
		
		_logger.debug("Company 2 Created %s" % self.Company2)

		_logger.debug("Setup Company 1")
		self.Company1.write({
			'rule_type':'so_and_po',
			'applicable_on': 'sale_purchase',
			'warehouse_id':self.env['stock.warehouse'].search([('company_id','=',self.Company1.id)]).id,
			'intercompany_user_id':1,
			'auto_validation':True,
			'using_interco_master_on_sale':True
		})
		self.Company2.write({
			'rule_type':'so_and_po',
			'applicable_on': 'sale_purchase',
			'warehouse_id':self.env['stock.warehouse'].search([('company_id','=',self.Company2.id)]).id,
			'intercompany_user_id':1,
			'auto_validation':True,
			'using_interco_master_on_sale':False

		})
		self.assertEqual(self.Company1.warehouse_id.id!=False, True, 'Company1.warehouse_id not defined')
		self.assertEqual(self.Company2.warehouse_id.id!=False, True, 'Company2.warehouse_id not defined')
		Companies = self.Company1+self.Company2

		_logger.debug("Creating Salesman 1")
		self.Salesman1 = User.create({
			'name':"Salesman 1",
			'login':'Salesman1',
			'email':'Salesman1@mail.com',
			'company_ids':[(6,0, self.Company1.ids)],
			'warehouse_ids':[(6,0,self.env['stock.warehouse'].with_context({'allowed_companies':self.Company1.ids}).search([('id','!=',False)]).ids)],
			'journal_ids':[(6,0,self.env['account.journal'].with_context({'allowed_companies':self.Company1.ids}).search([('id','!=',False)]).ids)],
			'company_id':self.Company1.id,
			'groups_id':[(6,0,[self.env.ref('base.group_user').id, self.env.ref('sales_team.group_sale_salesman').id])]
			})
		self.assertTrue(self.Salesman1.has_group('sales_team.group_sale_salesman'))
		self.assertTrue(len(self.Salesman1.warehouse_ids)>0)
		self.assertTrue(len(self.Salesman1.journal_ids)>0)
		self.assertEqual(len(self.Salesman1.company_ids), 1)
		_logger.debug("Salesman 1 Created %s" % (self.Salesman1))

		self.Salesman = self.Salesman1
		# END OF SALESMAN


		# START CREATING PRODUCT CATEGORIES
		self.ProductCategories = ProductCategory.create([{
			'name':'PRODUCT CAT 1',
			}, {
			'name':'PRODUCT CAT 2',
			}, {
			'name':'PRODUCT CAT 3',
			}])
		# END OF PRODUCT CATEGORIES

		self.CrmTeam1 = CrmTeam.create({
			'name':"CrmTeam1",
			'company_id':False,
			'product_category_ids':[(6,0,self.ProductCategories.ids)],
			'member_ids':[(6,0,self.Salesman.ids)]
			})

		self.Salesman1.write({'sale_team_ids':[(6,0,self.CrmTeam1.ids)]})

		self.Customer1 = Partner.create({
			'name': "Customer 1",
			'email': "Customer 1",
			'user_id': self.Salesman1.id,
			'can_direct_pickup':True
			})

		# CREATING DUMMY PRODUCT
		self.product1 = ProductTemplate.create({
			'name':"PRODUCT 1",
			'default_code':"P.001",
			'sale_ok':True,
			'purchase_ok':True,
			'list_price':'200',
			'tracking':'lot',
			'categ_id':self.ProductCategories[0].id,
			'type':'product',
			})


		self.Comp2Lot1 = self.env['stock.production.lot'].with_user(1).create({
			'name':"0000000111",
			'product_id':self.product1.product_variant_id.id,
			'company_id':self.Company2.id,
			})

		self.product1_comp2_quant = self.env['stock.quant'].with_user(1).create({
			'product_tmpl_id':self.product1.id,
			'product_id':self.product1.product_variant_id.id,
			'lot_id':self.Comp2Lot1.id,
			'location_id':self.Company2.warehouse_id.lot_stock_id.id,
			'inventory_quantity':2000,
			})


		def _prepare_line(order_obj, product_template):

			def run_onchange(new_obj,fields):
				for field_name, methods in new_obj._onchange_methods.items():
					if field_name in fields:
						new_obj._onchange_eval(field_name, '1', {})
				return new_obj
			data = {
				'order_id':order_obj,
				'product_id': product_template.product_variant_ids[0].id,
				'warehouse_id': self.Company1.warehouse_id.id,
				'company_id': self.Company1.id,
			}
			new_obj = self.env['sale.order.line'].with_user(self.Salesman1.id).new(data)
			new_obj = run_onchange(new_obj, ['product_id'])

			new_obj.update({'product_uom_qty':2})
			new_obj = run_onchange(new_obj, ['product_uom_qty'])

			new_obj_data = new_obj._convert_to_write({name:new_obj[name ] for name in new_obj._cache})

			return new_obj_data

		def _prepare_order_lines(order_obj):
			res = []
			res.append((0, 0, _prepare_line(order_obj, self.product1)))
			
			return res


		def _prepare_order(Customer):
			def run_onchange(new_obj,fields):
				for field_name, methods in new_obj._onchange_methods.items():
					if field_name in fields:
						new_obj._onchange_eval(field_name, '1', {})
				return new_obj

			data = {
				'partner_id': Customer.id,
				'pricelist_id': self.env.ref('product.list0').id,
				'state':'draft',
			}

			new_obj = SaleOrder.with_user(self.Salesman1.id).new(data)
			new_obj = run_onchange(new_obj, ['partner_id'])

			# new_obj.update({'order_line':})
			new_order_lines = _prepare_order_lines(new_obj)
			new_obj_data = new_obj._convert_to_write({name:new_obj[name ] for name in new_obj._cache})
			return new_obj_data


		# CREATING SALE ORDER
		# FOR COMPANY 1
		self.draft_sale_order1 = SaleOrder.with_user(self.Salesman1.id).create(_prepare_order(self.Customer1))


	# EXPECTED RESULT:
	# 	- so.state will still draft
	# 	- so.limit_approval_state will be not in ['approved','draft','rejected']


	def run_onchange(self, Obj, fields):
		for field_name, methods in Obj._onchange_methods.items():
			if field_name in fields:
				Obj._onchange_eval(field_name, '1', {})
		return Obj

	def _setup_intercompany_proc_order(self):
		self.draft_sale_order1.write({
			'interco_master':True,
			'plant_id':self.Company2.id,
			'vehicle_model_id':self.env.ref('sanqua_sale_flow.vehicle_model_fuso').id,
			'order_pickup_method_id':self.env.ref('sanqua_sale_flow.order_pickup_method_deliver').id,
			})

		self.run_onchange(self.draft_sale_order1, ['order_pickup_method_id'])

		self.draft_sale_order1.write({
			'team_id':self.CrmTeam1.id,
			})
		self.run_onchange(self.draft_sale_order1, ['team_id'])		


		self.assertEqual(self.draft_sale_order1.interco_master, True)
		self.assertEqual(self.draft_sale_order1.plant_id.id != False, True)
		self.assertEqual(self.draft_sale_order1.company_id.id != False, True)
		self.assertEqual(self.draft_sale_order1.team_id.id != False, True)


		self.assertEqual(self.draft_sale_order1.partner_can_direct_pickup, True)
		self.assertEqual(self.draft_sale_order1.direct_pickup_reduction_amount>=0.0,True)
		self.assertEqual(len(self.draft_sale_order1.order_line), 1)

	def process_interco_picking(self, sale):
		
		self.assertTrue(all(sale.picking_ids.mapped(lambda r:r.state=='confirmed')))
		with self.assertRaises(ValidationError):
			sale.picking_ids.action_assign() # make sure will raise error, because user must fill lot number first


		# fill lot
		for picking in sale.picking_ids:
			for move in picking.move_lines:
				not_full = True
				current_filled = 0.0
				interco_move_lines = []
				selected = self.env['stock.production.lot']
				while not_full:

					new_interco_move_line = {
						'move_id':move.id,
						'picking_id':move.picking_id.id,

					}
					new_obj = self.env['stock.interco.move.line'].new(new_interco_move_line)
					new_obj._default_warehouse()
					new_obj._compute_src_location_id()
					new_obj._compute_available_lot_in_location()
					curr = 0
					
					filtered_lots = new_obj.available_lot_in_location - selected
					self.assertTrue(len(filtered_lots)>0)
					curr_selected_lot = new_obj.available_lot_in_location[curr]
					selected += curr_selected_lot
					
					new_obj.update({
						'lot_id':curr_selected_lot.id
						})
					new_obj = self.run_onchange(new_obj, 'lot_id')
					

					if new_obj.free_qty>=move_id.product_uom_qty:
						qty = move_id.product_uom_qty
					else:
						qty = new_obj.free_qty
					
					new_obj.update({'qty':qty})
					current_filled += qty
					if current_filled >= move_id.product_uom_qty:
						not_full = False
					new_interco_move_line = new_obj._convert_to_write({name: new_obj[name] for name in new_obj._cache})
					interco_move_lines.append((0,0,new_interco_move_line))
				move.write({'interco_move_line_ids':interco_move_lines})




	def test_00_setup(self):
		
		self.assertTrue(self.Company1.using_interco_master_on_sale, msg=None)
		self.assertEqual(len(self.ProductCategories)==3, True)


		self.assertEqual(len(self.draft_sale_order1)==1,True)
		self.assertEqual(self.draft_sale_order1.state, 'draft')
		# self.assertTrue(len(self.draft_sale_order1.order_line)>0)
		# _logger.info((self.draft_sale_order1.order_line, self.draft_sale_order1.amount_total))


		self.assertEqual(len(self.draft_sale_order1.order_line), 1)

		self._setup_intercompany_proc_order()


		# try confirming
		self.assertEqual(self.draft_sale_order1.status_so,'2')
		

		self.assertEqual(self.draft_sale_order1.company_id.id, self.Salesman1.company_id.id)

		# try confirm with overlimit status
		self.draft_sale_order1.with_user(self.Salesman1.id).action_confirm()

		self.assertEqual(self.draft_sale_order1.status_so,'2')
		self.assertEqual(self.draft_sale_order1.limit_approval_state, 'need_approval_request')


		# test success make a request for approval limit
		self.draft_sale_order1.with_user(self.Salesman1.id).btn_request_approval_limit()
		self.assertEqual(self.draft_sale_order1.state, 'draft')
		self.assertEqual(self.draft_sale_order1.limit_approval_state,'need_approval') #must success changed to need_approval


		ApproverUser = self.env['res.users'].create({
			'name':"credit_approver1",
			'login':'credit_approver1',
			'email':'credit_approver1@mail.com',
			'company_ids':[(6,0, self.Salesman1.company_id.ids)],
			
			'warehouse_ids':[(6,0,self.Salesman1.warehouse_ids.ids)],
			'journal_ids':[(6,0,self.Salesman1.journal_ids.ids)],
			
			'company_id':self.Salesman1.company_id.id,
			'groups_id':[(6,0,[self.env.ref('base.group_user').id, self.env.ref('sanqua_sale_flow.group_credit_limit_approver').id])]
			})
		self.assertEqual(ApproverUser.company_id.id, self.Salesman1.company_id.id)

		with self.assertRaises(AccessError):
			self.draft_sale_order1.with_user(self.Salesman1.id).btn_approve_limit()

		self.assertEqual(self.draft_sale_order1.state, 'draft')
		self.assertEqual(self.draft_sale_order1.limit_approval_state, 'need_approval') #must failure to approving cause not authorized
		self.assertEqual(self.draft_sale_order1.warehouse_id.id!=False,True)

		self.draft_sale_order1.with_user(ApproverUser.id).btn_approve_limit()
		self.assertEqual(self.draft_sale_order1.state, 'done')
		self.assertEqual(self.draft_sale_order1.limit_approval_state, 'approved') #must failure to approving cause not authorized
		self.assertEqual(len(self.draft_sale_order1.picking_ids)>0, True)


		self.process_interco_picking(self.draft_sale_order1)