# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models
from datetime import timedelta

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sale_truck_mix_ids = fields.Many2many('sale.order.truck',related='sale_id.sale_truck_mix_ids' ,string='Sale Truck Mix Ref.',track_visibility='onchange')

    def _prepare_invoice(self,picking):
        invoice_vals = {
            'type': 'out_invoice',
            'invoice_origin': picking.name,
            'invoice_user_id': picking.sale_id.user_id.id,
            # Updated by : MIS@SanQua
            # At: 12/01/2022
            # Description: The date default is not include timezone.
            'invoice_date': (picking.date_done + timedelta(hours=7)),
            'invoice_origin': picking.doc_name,
            'narration': picking.note,
            'partner_id': picking.sale_id.partner_invoice_id.id,
            'partner_shipping_id': picking.partner_id.id,
            'team_id': picking.sales_team_id.id,
            # 'source_id': self.id,
            'invoice_line_ids':[],
            'invoice_payment_term_id':picking.sudo().sale_id.payment_term_id.id,
            'locked': False
        }
        for rec in picking.move_ids_without_package.filtered(lambda r:r.qty_to_invoice>0.0 and r.available_to_invoice and not r.product_id.reg_in_customer_stock_card):
            invoice_vals['invoice_line_ids'].append(
                    (0, 0, self._prepare_vals_move(rec))
                )
        
        # if picking.sale_id:
        #     reward_so_product = picking.sale_id._get_reward_lines().filtered(lambda r: r.qty_invoiced != r.product_uom_qty).mapped('product_id')
        #     reward_move_product = picking.move_ids_without_package.filtered(lambda r:r.qty_to_invoice>0.0).mapped('product_id')
        #     rewards_product = reward_so_product - reward_move_product
        #     for line in picking.sale_id._get_reward_lines().filtered(lambda r: r.product_id in rewards_product):
        #         invoice_vals['invoice_line_ids'].append(
        #                 (0, 0, self._prepare_vals_sale_order_line(line))
        #             )
        return invoice_vals