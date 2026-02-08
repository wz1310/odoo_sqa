# -*- coding: utf-8 -*-
"""MRP Product Forecast"""
from datetime import date, timedelta

from odoo import models, fields, api , _
from odoo.tools.float_utils import float_round
from odoo.exceptions import UserError

class MrpProductForecast(models.Model):
    _inherit = 'mrp.product.forecast'

    @api.constrains('forecast_qty', 'date', 'production_schedule_id')
    def constrains_forecast_product(self):
        for data in self:
            if data.forecast_qty >= 0 and self.env.context.get('mps'):
                rph_line_ids = self.env['mrp.rph.line'].search([('mrp_product_forecast_id', '=', data.id)])
                if rph_line_ids:
                    rph_line_id = rph_line_ids[0]
                    if rph_line_id and rph_line_id.mrp_rph_id:
                        if rph_line_id.mrp_rph_id.state == 'approved':
                            raise UserError(_("You should cancel %s before edit the forecast of the product" % (rph_line_id.mrp_rph_id.name)))
