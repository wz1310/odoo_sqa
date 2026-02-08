# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round, float_is_zero

class MrpdProductProduce(models.TransientModel):
    _inherit = "mrp.product.produce"

    def do_produce(self):
        """ Save the current wizard and go back to the MO. """
        production = self.env['mrp.production']
        lot = self.env['stock.production.lot']
        if self.code_production:
            # print("===============================")
            dt_lot = lot.search([('name', '=', self.code_production),('product_id','=',self.product_id.id)]).filtered(lambda r:r.company_id.id==self.company_id.id)
            # print("===============================",dt_lot)
            active_id = self.env.context.get('active_id')
            dt_production = production.browse(active_id)
            if not dt_lot:
                vals = {'name': self.code_production, 
                        'product_id': dt_production.product_id.id, 
                        'company_id': dt_production.company_id.id}
                dt_lot = lot.create(vals)
            self.finished_lot_id = dt_lot.id or False
        #Adi Remove
        check_lot = []
        for raw in self.raw_workorder_line_ids:
            prod_ids = self.raw_workorder_line_ids.filtered(lambda x: x.product_id.id == raw.product_id.id)
            sum_to_consume = sum(prod_ids.mapped('qty_to_consume'))
            sum_done = sum(prod_ids.mapped('qty_done'))
            if sum_to_consume > sum_done:
                raise UserError(_("Qty Consume tidak boleh lebih kecil dari Qty To Consume (BoM)\nProduct : %s\nTo Consume : %s \nConsume : %s" % (raw.product_id.name,sum_to_consume,sum_done)))
            quant = 0.0
            if raw.lot_id.id:
                quant = self.env['stock.quant'].search([('product_id', '=', raw.product_id.id),
                                                ('location_id', '=', dt_production.location_src_id.id),
                                                ('lot_id', '=', raw.lot_id.id)])
            # else:
            #     quant = self.env['stock.quant'].search([('product_id', '=', raw.product_id.id),
                                                # ('location_id', '=', dt_production.location_src_id.id)])
                if raw.qty_to_consume >= 0:
                    # if raw.qty_to_consume > raw.qty_done:
                    #     raise UserError(_("Kata Pak Mardi Haram lebih kecil"))
                    stock = quant.quantity
                # elif raw.qty_to_consume == 0:
                #     stock = quant.quantity - quant.reserved_quantity
            
                if raw.qty_done > stock:
                    raise UserError(_("Stock untuk Product %s \nLot : %s \nkurang dari yang dibutuhkan, Mohon periksa ketersediaan stock di %s\nStock Tersedia : %s\nDibutuhkan : %s\nKurang : %s") % (raw.product_id.name,raw.lot_id.name,dt_production.location_src_id.display_name,stock,raw.qty_done,stock-raw.qty_done))
                
                if raw.lot_id:
                    if raw.lot_id.id in check_lot:
                        raise UserError(_("Lot sudah di pilih untuk product yang sama %s" % (raw.lot_id.name)))
                    check_lot.append(raw.lot_id.id)
        self.ensure_one()
        self._record_production()
        self._check_company()
        return {'type': 'ir.actions.act_window_close'}

