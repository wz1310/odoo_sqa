# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    carton_sale = fields.Boolean(string='Carton Sale',default=False, track_visibility="onchange")

    @api.onchange('carton_sale')
    def _onchange_carton_sale(self):
        print("_onchange_carton_sale")
        if self.carton_sale:
            self.update({
                'interco_master':True,
                'order_line':[(5,0)],
            })
        else:
            self.interco_master = self.company_id.using_interco_master_on_sale


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    carton_sale = fields.Boolean("Carton Sale",default=False)

    @api.onchange('carton_sale')
    def _onchange_carton_sale(self):
        if self.carton_sale == True:
            category_ids = self.env['product.category'].search([('carton','=',True)])
            return {'domain':{'product_id':[('categ_id','in',category_ids.ids)]}}
        else:
            # return {'domain':{'product_id':[]}}
            for field_name, methods in self._onchange_methods.items():
                if field_name=='carton_sale':
                    continue
                self._onchange_eval(field_name, '1', {})
