# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class StockPicking1(models.Model):
    _inherit = 'stock.picking'

    def open_stockpick_substitute_wizard(self):
        form = self.env.ref('sanqua_substitute_delivery_order.stock_picking_substitute_view_form', raise_if_not_found=False)
        # context = self._context.copy()
        # context.update({'is_substitute':True})
        return {
                'name': _('Substitute Items'),
                'type': 'ir.actions.act_window',
                
                'view_mode': 'form',
                'res_model': 'stock.picking.substitute',
                'views': [(form.id, 'form')],
                'view_id': form.id,
                'target': 'new',
                # 'context': context,
            }

    sale_substitute_id = fields.Many2one('sale.order',string="SO Substitute Items", required=False, default=False)