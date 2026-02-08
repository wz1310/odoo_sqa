# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError,RedirectWarning,AccessError
from datetime import datetime, timedelta, date

class InheritSalesDivision(models.Model):
    _inherit = "crm.team"

    def open_p_category_line(self):
        return self.open_p_category_wizard()

    def open_p_category_wizard(self,datas=None):
        form = self.env.ref('mis_sales_division.open_p_category_wizard')
        self.ensure_one()
        context = dict(self.env.context or {})
        context.update({
            'active_id':self.id,
            'active_ids':self.ids
            })
        res = {
            'name': self.name+' '+"Product Categories",
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'show.p_category.wizard',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res


class SaleDiv(models.TransientModel):
    _name = 'show.p_category.wizard'

    @api.model
    def default_get(self,fields):
        res_id = self._context.get('active_id')
        model = self._context.get('active_model')
        Env = self.env[model]
        Record = Env.sudo().browse(res_id)

        res = super(SaleDiv,self).default_get(fields)
        res.update({'product_category_ids':[(6, 0, Record.product_category_ids.ids)]})
        return res


    product_category_ids = fields.Many2many('product.category')


    def confirm_reject(self):
        res_id = self._context.get('active_id')
        model = self._context.get('active_model')
        
        Env = self.env[model]
        Record = Env.sudo().browse(res_id)
        Record.update({'product_category_ids':[(6, 0, self.product_category_ids.ids)]})
        # self.env.cr.execute("""DELETE FROM crm_team_product_category_rel WHERE crm_team_id=%s""",(res_id,))
        # for x in self.product_category_ids:
        #     self.env.cr.execute("""INSERT INTO crm_team_product_category_rel("crm_team_id", "product_category_id")VALUES(%s, %s)""",(res_id,x.id))