# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
"""file payment log cancel"""
from odoo import fields, models, _
from odoo.exceptions import UserError


class PaymentLogCancel(models.TransientModel):
    _name = 'payment.log.cancel'
    _description = 'Payment Log Cancel'

    payment_ids = fields.Many2many('account.payment', 'account_payment_log_cancel_rel')
    reason = fields.Char()

    def apply_cancel(self):
        if self.reason:
            ctx = dict(self.env.context)
            if ctx.get('show_wizard_reason'):
                ctx['show_wizard_reason'] = False
            for sale in self.payment_ids:
                msg = _("Reason : %s") % (self.reason)
                sale.message_post(body=msg)
            return self.payment_ids.with_context(ctx).cancel()
        return False
