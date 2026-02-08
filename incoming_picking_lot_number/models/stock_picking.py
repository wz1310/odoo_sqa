from ast import literal_eval
from datetime import date
from itertools import groupby
from operator import itemgetter
import time

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError,ValidationError
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES

import logging
_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
	_inherit = 'stock.picking'


	date_received = fields.Datetime('Date Received', default=fields.Datetime.now)




class StockMove(models.Model):
	_inherit = 'stock.move'

	lot_serial_number = fields.Char('Lot/Serial Number', compute="get_default_value")

	@api.depends('picking_id','picking_id.date_received')
	def get_default_value(self):
		for each in self:
			date = each.picking_id.date_received
			if date:
				dd = date.day
				mm = date.month
				yy = date.year
				tgl = str(dd)+' '+str(mm)+' '+str(yy)[-2:]
				each.lot_serial_number = each.product_id.default_code + " / " + each.picking_id.name + " / " +str(tgl) 
			else:
				each.lot_serial_number == False
