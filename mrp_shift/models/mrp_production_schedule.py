# -*- coding: utf-8 -*-
"""MRP Production Schedule"""
from odoo import models, fields, api , _
from odoo.tools.float_utils import float_round
from datetime import date, timedelta

class MrpProductionSchedule(models.Model):
    _inherit = 'mrp.production.schedule'

    @api.model
    def get_mps_view_state(self, domain=False):
        """ Return the global information about MPS and a list of production
        schedules values with the domain.

        :param domain: domain for mrp.production.schedule
        :return: values used by the client action in order to render the MPS.
            - dates: list of period name
            - production_schedule_ids: list of production schedules values
            - manufacturing_period: list of periods (days, months or years)
            - company_id: user current company
            - groups: company settings that hide/display different rows
        :rtype: dict
        """
        res = super(MrpProductionSchedule, self).get_mps_view_state(domain)
        res.get('groups')[0]['manufacturing_period']= self.env.company.manufacturing_period
        res.get('groups')[0]['manufacturing_period_to_display']= self.env.company.manufacturing_period_to_display
        return res

    def set_forecast_qty(self, date_index, quantity):
        """ Save the forecast quantity:

        params quantity: The new total forecasted quantity
        params date_index: The manufacturing period
        """
        res = super(MrpProductionSchedule, self).set_forecast_qty(date_index, quantity)
        self.ensure_one()
        date_start, date_stop = self.company_id._get_date_range()[date_index]
        domain = [('date','>=', date_start), ('date','<=', date_stop), ('production_schedule_id', '=', self.id)]
        forecast = self.env['mrp.product.forecast']
        existing_forecast = forecast.search(domain, order='date asc')
        existing_forecast.unlink()
        delta = (date_stop) - date_start
        data_date = []  
        for i in range(delta.days + 1):
            if date_start + timedelta(days=i) not in data_date:
                data_date.append(date_start + timedelta(days=i))
        delta = delta+ timedelta(days=1)
        new_qty = 0
        if quantity > 0:
            new_qty = int(quantity/delta.days)
        new_qty = float_round(new_qty, precision_rounding=self.product_uom_id.rounding)
        # range date
        change_value = False
        i = 1
        qty_must_done = quantity
        qty_check = 0
        for data_tgl in data_date:
            if i == len(data_date):
                forecast.create({
                    
                    'forecast_qty': qty_must_done - qty_check,
                    'date': data_tgl,
                    'replenish_qty': 0,
                    'production_schedule_id': self.id
                })
            else:
                # if data_tgl in existing_forecast.mapped('date'):
                #     change_value = True
                # else:
                forecast.create({
                    'forecast_qty': new_qty,
                    'date': data_tgl,
                    'replenish_qty': 0,
                    'production_schedule_id': self.id
                })
            qty_check += new_qty
            i += 1
        # if change_value:
        #     existing_forecast.with_context(mps=True).write({'forecast_qty': new_qty})
        return res