# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError

import logging
_logger = logging.getLogger(__name__)


class OrderPickupMethod(models.Model):
	_name = 'order.pickup.method'
	_description = 'Order Pickup Method'


	name = fields.Char(
		string='Name',
		required=True,
		readonly=False,
		index=True,
		default=None,
		help="Pickup Method Name",
		size=50,
		translate=True
	)


	description = fields.Text(
	    string='Description',
	    required=False,
	    readonly=False,
	    index=False,
	    default=None,
	    help=False,
	    translate=True
	)

	price_unit_discount_agreement = fields.Boolean(default=False, string="Price Unit Discount (Agreement)", help="If this checked, and when customer choose this method on pickup method will reduce unit price (likely discount) but directly on unit price.")

	
	active = fields.Boolean('Active', default=True)