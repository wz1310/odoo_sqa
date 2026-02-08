# -*- coding: utf-8 -*-

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.addons.sale.tests.test_sale_order import TestSaleOrder

import logging
_logger = logging.getLogger(__name__)

# @tagged('-standard', 'nice')
@tagged('post_install', 'at_install')
class TestIntercompanyProcurementOrder(TestSaleOrder):
	@classmethod
	def setUpClass(cls):
		super(TestIntercompanyProcurementOrder, cls).setUpClass()


	def test_sale_order(self):
		# Bellow, is example of test create with user group that setted up in setUp()
		super(TestIntercompanyProcurementOrder, self).test_sale_order()
		sale_order_company = self.sale_order.company_id
		other_company = self.env['res.company'].search([('id','not in',sale_order_company.ids)])
		self.sale_order.write({'interco_company_id':other_company[0].id})

		self.assertTrue(self.sale_order.interco_company_id.id!=False, msg=None)
		self.assertNotEqual(self.sale_order.interco_company_id, self.sale_order.company_id, msg=None)

		self.sale_order.create_interco_purchase_order()
		_logger.info((';;;;;;;', self.sale_order.interco_purchase_id))
		self.assertEqual(len(self.sale_order.interco_purchase_id.ids),1, msg=None)
