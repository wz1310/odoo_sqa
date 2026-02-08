# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang


class pundi_PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    confirm_id = fields.Many2one('res.users','Confirm By',required=False,copy=False)

    # def button_approve(self, force=False):
    #     self.write({'state': 'purchase', 
    #                 'date_approve': fields.Date.context_today(self),
    #                 'confirm_id':self.env['res.users'].browse(self.env.uid)
    #                })
    #     self.filtered(lambda p: p.company_id.po_lock == 'lock').write({'state': 'done'})
    #     return {}

    def button_approve(self, force=False):
        result = super(pundi_PurchaseOrder, self).button_approve(force=force)
        self.confirm_id=self.env.uid
        self._create_picking()
        return result

    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step'\
                    or (order.company_id.po_double_validation == 'two_step'\
                        and order.amount_total < self.env.company.currency_id._convert(
                            order.company_id.po_double_validation_amount, order.currency_id, order.company_id, order.date_order or fields.Date.today()))\
                    or order.user_has_groups('pundi_purchase.group_purchase_corporate'):
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
        return True

    
