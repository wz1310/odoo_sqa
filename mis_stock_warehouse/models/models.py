# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError,RedirectWarning,AccessError

class StockWarehouseInherit(models.Model):
    _inherit = 'stock.warehouse'

    wh_address = fields.Text(string='Warehouse Address')