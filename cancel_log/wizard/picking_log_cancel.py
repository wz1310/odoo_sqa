# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
"""file picking log cancel"""
from datetime import datetime

from odoo import fields, models, _
from odoo.exceptions import UserError


class PickingLogCancel(models.TransientModel):
    _name = 'picking.log.cancel'
    _description = 'Picking Log Cancel'

    picking_ids = fields.Many2many('stock.picking', 'picking_log_cancel_rel')
    reason = fields.Char()

    def apply_cancel(self):
        if self.reason:
            ctx = dict(self.env.context)
            if ctx.get('show_wizard_reason'):
                ctx['show_wizard_reason'] = False
            
            for picking in self.picking_ids:
                reason = picking.cancel_note
                if reason:
                    picking.cancel_note = reason +'\n'+datetime.now().date().strftime("%d-%m-%Y") + ' by '+ self.env.user.name +' : '+self.reason
                else:
                    picking.cancel_note = datetime.now().date().strftime("%d-%m-%Y") + ' by '+ self.env.user.name +' : '+self.reason
                msg = _("Reason : %s") % (self.reason)
                picking.message_post(body=msg)
            return self.picking_ids.with_context(ctx).action_cancel()
        return False
