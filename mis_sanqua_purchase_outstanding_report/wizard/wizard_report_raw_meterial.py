# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
import logging
_logger = logging.getLogger(__name__)
import base64
from datetime import date
from io import BytesIO
from calendar import monthrange
from odoo.exceptions import ValidationError
try:
	from odoo.tools.misc import xlsxwriter
except ImportError:
	import xlsxwriter

class WizardRawMaterialReport(models.TransientModel):
	_inherit = 'wizard.purchase.order.raw.material.report'

	whs = fields.Many2one('stock.warehouse',string='Warehouse')
	filter_date = fields.Selection([('efc_d','Effective Date'),('rcv_d','Receive Date')],string='Filter Date By', default='efc_d')