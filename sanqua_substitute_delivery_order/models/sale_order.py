# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    is_substitute_order = fields.Boolean(string="Is Substitute Order", default=False)
    substitute_order_id = fields.Many2one('sale.order',string="Substitute Order")
    substitute_with_order_id = fields.Many2one('sale.order', string="New Order(Substitute)", help="New Order (Subtitute with)")


    # def action_confirming_subtitute_order(self):
    #     if self.substitute_order_id:
    #         old_order = self.with_user(self.company_id.intercompany_user_id).substitute_order_id
    #         old_order.picking_ids.action_cancel() #older order will be canceled
    #         return super(SaleOrder, self.with_context(ORIGINAL_CONFIRM=True)).action_confirm()

    # def action_confirm(self):
    #     res = False
    #     if self.substitute_order_id:
    #         self.action_confirming_subtitute_order()
    #     else:
    #         # origin confirm
    #         res = super().action_confirm()
    #     return res


    def btn_approve_limit(self):
        res = super(SaleOrder, self).btn_approve_limit()
        old_order = self.with_user(self.company_id.intercompany_user_id).substitute_order_id
        if old_order:
            old_order.with_user(self.env.user).btn_cancel_approval() #older order will be canceled
        return res

    def btn_reject_limit(self):
        res = super(SaleOrder, self).btn_reject_limit()
        old_picking_with_subtitue_id = self.env['stock.picking'].sudo().search([('sale_substitute_id', '=', self.id)])
        old_picking_with_subtitue_id.sudo().write({'sale_substitute_id': False})
        return res
