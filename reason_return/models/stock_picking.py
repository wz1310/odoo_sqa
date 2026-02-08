# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class StockPicking(models.Model):
	_inherit = "stock.picking"

	reason = fields.Text(string="Reason")