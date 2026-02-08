from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import operator as Operator		
import logging
_logger = logging.getLogger(__name__)
class Product(models.Model):
    _inherit = 'product.product'

    safety_qty = fields.Float(string="Safety Qty",digits="Product Unit Of Measure" , groups="purchase.group_purchase_manager", track_visibility='onchange')
    qty_not_safe = fields.Boolean("Under Minimum Qty", compute="_compute_qty_not_safe", search="_search_qty_not_safe", groups="purchase.group_purchase_manager", track_visibility='onchange')

    @api.constrains('safety_qty')
    def constrains_safe_qty(self):
        # update only if product variant template only just has 1
        
        ctx_params = self._context.get('params')
        execute = False
        if ctx_params:
            if ctx_params.get('model')=='product.template':
                execute = False
            else:
                execute = True
        else:
            execute = True
        
        if execute:
            for rec in self:
                if len(rec.product_tmpl_id.product_variant_ids)==1:
                    rec.with_context(pass_safe_qty_constrains=True).product_tmpl_id.update({'safety_qty':rec.safety_qty})
    
    @api.depends('qty_available','safety_qty')
    def _compute_qty_not_safe(self):
        for each in self:
            if each.qty_available < each.safety_qty:
                each.qty_not_safe = True
            else:
                each.qty_not_safe = False

    def _search_qty_not_safe(self, operator, value):
        fun = False
        self = self.search([])
        if operator=='=':
            fun = Operator.le
            if value==False:
                fun = Operator.ge
        elif operator == '!=':
            fun = Operator.ge
            if value==False:
                fun = Operator.gt
        if fun!=False:

            product = self.filtered(lambda r:fun(r.qty_available,r.safety_qty))
            return [('id','in',product.ids)]

        return []

    def _send_notif_non_safe_qty(self):
        list_product_ids = []
        domain = self._search_qty_not_safe('=',True)
        records = self.search(domain)
        for alert in records:
            company = self.env.company
            partner_ids = self.env['res.company'].search([('id','=',company.id)]).mapped(lambda r:r.safety_qty_alert_partner_ids)
            value = "\
                <h1>STOCK ALERT</h1>\
                Product : %s<br/>\
                Current Available Qty : %s pcs</br>\
                Safety Qty : %s pcs<br/>\
                <br/>\
                Please reorder to safe current available stock" % (alert.product_tmpl_id.name,alert.qty_available,alert.safety_qty)
            if len(partner_ids):
                alert.message_notify(body=value, partner_ids=partner_ids.ids)
            
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    safety_qty = fields.Float(string="Safety Qty",digits="Product Unit Of Measure", groups="purchase.group_purchase_manager", track_visibility='onchange')
    qty_not_safe = fields.Boolean("Under Minimum Qty", compute="_compute_qty_not_safe", search="_search_qty_not_safe", groups="purchase.group_purchase_manager", track_visibility='onchange')

    @api.depends('safety_qty')
    def _compute_qty_not_safe(self):
        for rec in self:
            res = False
            if any(rec.product_variant_ids.mapped(lambda r:r.qty_not_safe)):
                res = True
            rec.qty_not_safe = res

    def _search_qty_not_safe(self, operator, value):
        fun = False
        self = self.search([])
        if operator=='=':
            fun = Operator.le
            if value==False:
                fun = Operator.ge
        elif operator == '!=':
            fun = Operator.ge
            if value==False:
                fun = Operator.gt
        if fun!=False:

            product = self.filtered(lambda r:fun(r.qty_available,r.safety_qty))
            return [('id','in',product.ids)]

        return []

    @api.constrains('safety_qty')
    def _constrains_safety_qty(self):
        
        if not self._context.get('pass_safe_qty_constrains'):
            for each in self:
                for product in each.product_variant_ids:
                    product.write({'safety_qty': each.safety_qty})
    