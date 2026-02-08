# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
"""file sale log cancel"""
from datetime import datetime

from odoo import fields, models, _
from odoo.exceptions import UserError


class SaleLogCancel(models.TransientModel):
    _name = 'sale.log.cancel'
    _description = 'Sale Log Cancel'

    sale_ids = fields.Many2many('sale.order', 'sale_order_log_cancel_rel')
    reason = fields.Char()

    def apply_cancel(self):
        if self.reason:
            ctx = dict(self.env.context)
            if ctx.get('show_wizard_reason'):
                ctx['show_wizard_reason'] = False
            
            for sale in self.sale_ids:
                reason = sale.cancel_note
                if reason:
                    sale.cancel_note = reason +'\n'+datetime.now().date().strftime("%d-%m-%Y") + ' by '+ sale.user_id.name +' : '+self.reason
                else:
                    sale.cancel_note = datetime.now().date().strftime("%d-%m-%Y") + ' by '+ sale.user_id.name +' : '+self.reason
                msg = _("Reason : %s") % (self.reason)
                sale.message_post(body=msg)
            return self.sale_ids.with_context(ctx).action_cancel()
        return False
