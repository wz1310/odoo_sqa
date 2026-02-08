# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError,RedirectWarning,AccessError
from datetime import datetime, timedelta, date

MONTH_SELECTION = [
    ('1', 'Januari'),
    ('2', 'Februari'),
    ('3', 'Maret'),
    ('4', 'April'),
    ('5', 'Mei'),
    ('6', 'Juni'),
    ('7', 'Juli'),
    ('8', 'Agustus'),
    ('9', 'September'),
    ('10', 'Oktober'),
    ('11', 'November'),
    ('12', 'Desember'),
]

class StandarHarga(models.Model):
    """ Create new model Sale Forecast """
    _name = "standar.harga"
    _description = "Standar Harga"
    _rec_name = "product_id"


    def get_years():
        """ Function to get list of years """
        year_list = []
        for i in range(2021, 2100):
            selection_string = str(i)
            year_list.append((selection_string, str(i)))
        return year_list

    # product_category_id = fields.Many2one('product.category')
    product_id = fields.Many2one('product.template')
    year = fields.Selection(get_years())
    month = fields.Selection(MONTH_SELECTION)
    standar_harga = fields.Float()
    logs = fields.Text(string="Logs", default="")
    # forecast_qty = fields.Float(string='Total Value')
    # forecast_value = fields.Float()


    # @api.onchange('product_category_id')
    # def _onchange_product_category_id(self):
    #     """ Function to dynamically change domain for product_id value based on product category """
    #     for rec in self:
    #         domain = {}
    #         if rec.product_category_id:
    #             domain = {'domain': {'product_id': [('categ_id', '=', rec.product_category_id.id)]}}
    #             return domain

    def write(self,vals):
        log_prod = ''
        log_standar_harga = ''
        log_month = ''
        log_year = ''
        if 'standar_harga' in vals:
            log_standar_harga ='\n'+'Change Standar Harga : '+str(self.standar_harga)+' -> '+str(vals['standar_harga'])
        if 'product_id' in vals:
            log_prod ='\n'+'Change Product : '+str(self.product_id.name)+' -> '+str(self.env['product.template'].browse(vals['product_id']).name)
        if 'month' in vals:
            log_month ='\n'+'Change Month : '+str(self.month)+' -> '+str(vals['month'])
        if 'year' in vals:
            log_year ='\n'+'Change Year : '+str(self.year)+' -> '+str(vals['year'])
        if vals:
            vals.update({
                'logs':str(self.logs)+'\n'+
                str(fields.Datetime.context_timestamp(self, datetime.now()).strftime("%d-%m-%Y %H:%M"))
                +'\n'+self.env.user.name
                +log_standar_harga
                +log_prod
                +log_month
                +log_year
                +'\n'+"========================================="
                if self.logs
                else
                str(fields.Datetime.context_timestamp(self, datetime.now()).strftime("%d-%m-%Y %H:%M"))
                +'\n'+self.env.user.name
                +log_standar_harga
                +log_prod
                +log_month
                +log_year
                +'\n'+"========================================="
                })
        return super(StandarHarga, self).write(vals)

    def open_wizard(self,datas=None):
        form = self.env.ref('mis_sales_forecast.open_logs_wizard')
        self.ensure_one()
        context = dict(self.env.context or {})
        context.update({
            'active_id':self.id,
            'active_ids':self.ids,
            'default_logs':self.logs
            })
        res = {
            'name': self.product_id.name,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'show.logs.wizard',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res


class SaleForecastWizard(models.TransientModel):
    _name = 'show.logs.wizard'


    logs = fields.Text()
