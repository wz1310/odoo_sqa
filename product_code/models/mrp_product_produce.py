# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round, float_is_zero

class MrpProductProduce(models.TransientModel):
    _inherit = "mrp.product.produce"

    code_production = fields.Char(string="Kode Produksi")

    @api.model
    def default_get(self, fields):
        res = super(MrpProductProduce, self).default_get(fields)
        production = self.env['mrp.production']
        production_id = self.env.context.get('default_production_id') or self.env.context.get('active_id')
        if production_id:
            production = self.env['mrp.production'].browse(production_id)
        if production.exists():
            res['code_production'] = production.code_production
        return res

    def do_produce(self):
        """ Save the current wizard and go back to the MO. """
        production = self.env['mrp.production']
        lot = self.env['stock.production.lot']
        if self.code_production:
            dt_lot = lot.search([('name', '=', self.code_production),('product_id','=',self.product_id.id)])
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
        return super(MrpProductProduce, self).do_produce()

    # @api.model
    # def _generate_lines_values(self, move, qty_to_consume):
    #     """ Create workorder line. First generate line based on the reservation,
    #     in order to prefill reserved quantity, lot and serial number.
    #     If the quantity to consume is greater than the reservation quantity then
    #     create line with the correct quantity to consume but without lot or
    #     serial number.
    #     """
    #     lines = []
    #     is_tracked = move.product_id.tracking == 'serial'
    #     if move in self.move_raw_ids._origin:
    #         # Get the inverse_name (many2one on line) of raw_workorder_line_ids
    #         initial_line_values = {self.raw_workorder_line_ids._get_raw_workorder_inverse_name(): self.id}
    #     else:
    #         # Get the inverse_name (many2one on line) of finished_workorder_line_ids
    #         initial_line_values = {self.finished_workorder_line_ids._get_finished_workoder_inverse_name(): self.id}
    #     for move_line in move.move_line_ids:
    #         line = dict(initial_line_values)
    #         if float_compare(qty_to_consume, 0.0, precision_rounding=move.product_uom.rounding) <= 0:
    #             break
    #         # move line already 'used' in workorder (from its lot for instance)
    #         if move_line.lot_produced_ids or float_compare(move_line.product_uom_qty, move_line.qty_done, precision_rounding=move.product_uom.rounding) <= 0:
    #             continue 
    #         # search wo line on which the lot is not fully consumed or other reserved lot
    #         linked_wo_line = self._workorder_line_ids().filtered(
    #             lambda line: line.move_id == move and
    #             line.lot_id == move_line.lot_id
    #         )
    #         if linked_wo_line:
    #             if float_compare(sum(linked_wo_line.mapped('qty_to_consume')), move_line.product_uom_qty - move_line.qty_done, precision_rounding=move.product_uom.rounding) < 0:
    #                 to_consume_in_line = min(qty_to_consume, move_line.product_uom_qty - move_line.qty_done - sum(linked_wo_line.mapped('qty_to_consume')))
    #             else:
    #                 continue
    #         else:
    #             to_consume_in_line = min(qty_to_consume, move_line.product_uom_qty - move_line.qty_done)
    #         line.update({
    #             'move_id': move.id,
    #             'product_id': move.product_id.id,
    #             'product_uom_id': is_tracked and move.product_id.uom_id.id or move.product_uom.id,
    #             'qty_to_consume': to_consume_in_line,
    #             'qty_reserved': to_consume_in_line,
    #             'lot_id': move_line.lot_id.id,
    #             'qty_done': to_consume_in_line,
    #         })
    #         lines.append(line)
    #         qty_to_consume -= to_consume_in_line
    #     # The move has not reserved the whole quantity so we create new wo lines
    #     if float_compare(qty_to_consume, 0.0, precision_rounding=move.product_uom.rounding) > 0:
    #         line = dict(initial_line_values)
    #         if move.product_id.tracking == 'serial':
    #             while float_compare(qty_to_consume, 0.0, precision_rounding=move.product_uom.rounding) > 0:
    #                 line.update({
    #                     'move_id': move.id,
    #                     'product_id': move.product_id.id,
    #                     'product_uom_id': move.product_id.uom_id.id,
    #                     'qty_to_consume': 1,
    #                     'qty_done': 1,
    #                 })
    #                 lines.append(line)
    #                 qty_to_consume -= 1
    #         else:
    #             for move_line in move.move_line_ids.sorted('id'):
    #                 line = dict(initial_line_values)
    #                 line.update({
    #                     'move_id': move.id,
    #                     'product_id': move.product_id.id,
    #                     'product_uom_id': move.product_uom.id,
    #                     'qty_to_consume': qty_to_consume,
    #                     'qty_done': move_line.qty_done,
    #                     'lot_id': move_line.lot_id.id,
    #                 })
    #                 lines.append(line)
    #     return lines

class MrpProductProduceLine(models.TransientModel):
    _inherit = "mrp.product.produce.line"

    available_lot_in_location = fields.Many2many('stock.production.lot', compute="_check_available_lot", string="Available Lot", context={'all_companies':True})

    @api.depends('move_id','product_id')
    def _check_available_lot(self):
		# if self.move_id.picking_type_id.code == 'internal':
        production = self.env['mrp.production']
        active_id = self.env.context.get('active_id')
        dt_production = production.browse(active_id)
        if dt_production:
            Lot = self.env['stock.production.lot']
            for rec in self.sudo():
                # ProductLot = Lot.with_user(rec.move_id.company_id.intercompany_user_id.id).search([('product_id','=',rec.product_id.id), ('company_id','=',rec.warehouse_id.company_id.id)])
                AvailableLot = self.env['stock.production.lot']
                # ProductProduct = self.env['product.product'].search([('id','in',ProductLot.mapped('product_id.id'))])
                quant_ids = self.env['stock.quant'].search([('product_id', '=', rec.product_id.id),
                                                                ('location_id', '=', dt_production.location_src_id.id)])
                for quant in quant_ids:
                    available = quant.quantity
                    if available > 0.0:
                        AvailableLot += quant.lot_id
                rec.update({
                    'available_lot_in_location':[(6,None, AvailableLot.ids)]
                    })

    @api.constrains('lot_id')
    def _check_validity_lot(self):
        """ verifies lot only can input one time"""
        data_lot = []
        for product_lot in self:
            if product_lot.lot_id:
                if product_lot.lot_id.id in data_lot:
                    raise UserError(_("Lot sudah di pilih untuk product yang sama %s" % (product_lot.lot_id.name)))
                data_lot.append(product_lot.lot_id.id)
