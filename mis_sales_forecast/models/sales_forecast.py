# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError,RedirectWarning,AccessError
from datetime import datetime, timedelta, date


class InherSalesForecast(models.Model):
    _inherit = 'sale.forecast'
    
    rev_qty = fields.Integer(string="Rev. Qty")
    logs = fields.Text(string="Logs", default="")
    product_category_id = fields.Many2one('product.category', related='product_id.categ_id')

    def write(self,vals):
        log_rev = ''
        log_prod = ''
        log_prod_categ = ''
        log_month = ''
        log_comp = ''
        log_fq = ''
        log_year = ''
        if 'product_category_id' in vals:
            log_prod_categ ='\n'+'Change Product Category : '+str(self.product_category_id.name)+' -> '+str(self.env['product.category'].browse(vals['product_category_id']).name)
        if 'product_id' in vals:
            log_prod ='\n'+'Change Product : '+str(self.product_id.name)+' -> '+str(self.env['product.template'].browse(vals['product_id']).name)
        if 'rev_qty' in vals:
            log_rev ='\n'+'Change Rev Qty : '+str(self.rev_qty)+' -> '+str(vals['rev_qty'])
        if 'month' in vals:
            log_month ='\n'+'Change Month : '+str(self.month)+' -> '+str(vals['month'])
        if 'year' in vals:
            log_year ='\n'+'Change Year : '+str(self.year)+' -> '+str(vals['year'])
        if 'company_id' in vals:
            log_comp ='\n'+'Change Company : '+str(self.company_id.name)+' -> '+str(self.sudo().env['res.company'].browse(vals['company_id']).name)
        if 'forecast_qty' in vals:
            log_fq ='\n'+'Change Forecast Qty : '+str(self.forecast_qty)+' -> '+str(vals['forecast_qty'])
        if vals:
            vals.update({
                'logs':str(self.logs)+'\n'+
                str(fields.Datetime.context_timestamp(self, datetime.now()).strftime("%d-%m-%Y %H:%M"))
                +'\n'+self.env.user.name
                +log_prod_categ
                +log_rev
                +log_prod
                +log_month
                +log_comp
                +log_year
                +log_fq
                +'\n'+"========================================="
                if self.logs
                else
                str(fields.Datetime.context_timestamp(self, datetime.now()).strftime("%d-%m-%Y %H:%M"))
                +'\n'+self.env.user.name
                +log_prod_categ
                +log_rev
                +log_prod
                +log_month
                +log_comp
                +log_year
                +log_fq
                +'\n'+"========================================="
                })
        return super(InherSalesForecast, self).write(vals)

    # def open_wizard(self,datas=None):
    #     return{
    #     'name': '',
    #     'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
    #     'res_model': 'sale.forecast',
    #     'type': 'ir.actions.act_window',
    #     'view_mode': 'tree,form',
    #     'view_type': 'tree',
    #     'target':'new',
    #     'limit': 80,
    #     'context': {
    #     'default_logs': self.logs,
    #     }
    #     }

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
            'name': self.product_category_id.name,
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

    # @api.model
    # def default_get(self,fields):
    #     res_id = self._context.get('active_id')
    #     model = self._context.get('active_model')
    #     Env = self.env[model]
    #     Record = Env.sudo().browse(res_id)

    #     res = super(SaleDiv,self).default_get(fields)
    #     res.update({'product_category_ids':[(6, 0, Record.product_category_ids.ids)]})
    #     return res


    logs = fields.Text()


    # def confirm_reject(self):
    #     res_id = self._context.get('active_id')
    #     model = self._context.get('active_model')
        
    #     Env = self.env[model]
    #     Record = Env.sudo().browse(res_id)
    #     Record.update({'product_category_ids':[(6, 0, self.product_category_ids.ids)]})