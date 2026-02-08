from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round
import logging
_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"


    def _create_return_move_lines(self, source_picking, active_picking):
        """
            _params self : Return picking created.
            _params source_picking : picking origin from SO/PO.
            _params active_picking : origin picking from WIM.
        """
        _logger.error('>>> stock_picking_return_reason/models/stock_picking.py def _create_return_move_lines(self, source_picking, active_picking):')
        _logger.error('----------------------------------------------------------------------------------------------------------------------------')
        _logger.error('>>> source_picking: ' + str(source_picking))
        _logger.error('>>> active_picking: ' + str(active_picking))
        # print('>>> active_picking.move_line_ids.id : ' + str(active_picking.move_line_ids.id))

        self.ensure_one()
        # self --> picking to be process
        # source_picking --> picking in intercompany on processing

        LotNotFound = []
        # for move in self.move_lines:
        #     # loop each moves
        #     # find matched move from source_picking with equal product
        #     matched = source_picking.sudo().move_lines.filtered(lambda r:r.product_id.id == move.product_id.id)
        #     if not len(matched):
        #         raise UserError(_("Failed on finding same product: %s in %s on source:%s") % (move.sudo().product_id.display_name, self.sudo().display_name, source_picking.sudo().display_name))
        #     # loop each move_line_ids in source_picking

        # loop each move_line_ids in source_picking
        if len(self.move_line_ids):
            self.move_line_ids.unlink()
        move_line_ids = []
        line_done = active_picking.move_line_ids.filtered(
            lambda r: r.qty_done > 0.0)
        # _logger.error('>>> move_line_multi : ' + str(line_done.move_id.name))
        # move_line_multi = line_done.move_id.name
        # print(">>>>>>>>>>>>>>>>>>>",move_line_multi)
        # _logger.error('>>> move_multi : ' + str(line_done.move_id))
        _logger.error('>>> line_done : ' + str(line_done))
        _logger.error('>>> move_line_ids : ' + str(move_line_ids))
        if not len(line_done):
            raise UserError(_("Please set done qty at least for 1 item!"))
        for line in line_done.sorted('qty_done'):
            # matched possibilities will be not a single

            # Untuk mendapatkan stock move dari picking (SJ)
            line_source = source_picking.mapped('move_ids_without_package').filtered(
                lambda r: r.product_id.id == line.product_id.id and r.product_uom_qty == line.move_id.move_orig_ids.product_uom_qty and r.name == line.move_id.name)
            # line_sources = source_picking.mapped('move_ids_without_package').filtered(
            #     lambda r: r.product_id == line.product_id and r.product_uom_qty == line.move_id.move_orig_ids.product_uom_qty and r.desc_product == move_line_multi)
            print("LINEs ", line)
            print("LINE ", line_done.sorted('qty_done'))
            print("LINE SOURCE", len(line_source))
            print("LINE SOURCE",line_source)
            # _logger.error('>>> line_source not filtered : ' + str(source_picking))
            # _logger.error('>>> line_source filtered: ' + str(line_source))
            # if len(line_source)>1:
            #     gap = line_source.filtered(lambda r: r.name == line.move_id.name)
            #     print("GAPPP", line.move_id.name)
            #     print("GAPPP", gap)
                # current_return_qty = line_source.product_uom_qty - \
                # sum(line_source.move_dest_ids.filtered(
                #     lambda r: r.state == 'done').mapped('product_uom_qty'))
            current_return_qty = line_source.product_uom_qty - \
                sum(line_source.move_dest_ids.filtered(
                    lambda r: r.state == 'done').mapped('product_uom_qty'))
            # _logger.error('>>> line_source.product_uom_qty : ' + str(current_return_qty))
            # _logger.error('>>> sum : ' + str(sum(line_source.move_dest_ids.filtered(
            #         lambda r: r.state == 'done').mapped('product_uom_qty'))))
            # _logger.error('>>> current_return_qty : ' + str(current_return_qty))
            matched = self.sudo().move_lines.filtered(lambda r: r.product_id.id ==
                                                      line.product_id.id and r.product_uom_qty == current_return_qty and r.name == line.move_id.name)
            print('>>> matched : ' + str(matched))
            _logger.error('>>> matched : ' + str(matched))
            MoveLine = self.env['stock.move.line']

            # Lot = self.env['stock.production.lot'].search([('company_id','=',self.sudo().company_id.id), ('name','=',line.sudo().lot_id.name), ('product_id','=',line.sudo().product_id.id)])
            Lot = self.env['stock.production.lot'].fetch_company_lot(
                line.sudo().lot_id, self.sudo().company_id)
            _logger.error('>>> name: ' + str(line.sudo().lot_id.name))
            _logger.error('>>> product_id: ' + str(line.sudo().lot_id.product_id.id))
            _logger.error('>>> product_id: ' + str(self.sudo().company_id.id))
            _logger.error('>>> Lot: ' + str(Lot))

            if not len(Lot):
                LotNotFound.append("%s | %s | %s" % (line.sudo(
                ).lot_id.name, line.product_id.display_name, self.sudo().company_id.display_name,))
                continue

            _logger.error('>>> Start write stock.move.line...')
            if not len(LotNotFound):
                new_mvl = dict(
                    product_id=line.sudo().product_id.id,
                    product_uom_id=line.sudo().product_id.uom_id.id,
                    picking_id=self.sudo().id,
                    move_id=line.sudo().move_id.id,
                    lot_id=Lot.sudo().id,
                    qty_done=line.sudo().qty_done,

                    # PCI Version
                    # location_dest_id=self.sudo().location_id.id,
                    # location_id=self.sudo().location_dest_id.id,

                    # MIS@SanQua Update
                    # Date: 13/10/2021
                    # Note: This update purpose is to handle journal of WIM/GR (from customer) that not correct.
                    location_dest_id=self.sudo().location_dest_id.id,
                    location_id=self.sudo().location_id.id,
                    company_id=self.sudo().company_id.id)
                # move_line_ids.append((0, 0, new_mvl))
                matched.write({'move_line_ids': [(0, 0, new_mvl)]})
            _logger.error('>>> data : ' + str(new_mvl))
            # _logger.error('>>> move_line_id : ' + str(matched.id))
            # _logger.error('>>> move_id : ' + str(line.sudo().move_id.id))
            # _logger.error('>>> location_dest_id : ' + str(self.sudo().location_id.id))
            # _logger.error('>>> location_id : ' + str(self.sudo().location_dest_id.id))
            # _logger.error('>>> End write stock.move.line...')
        if len(LotNotFound):
            raise UserError(_("Failed to fetch Lot, please check:\n%s") % (
                "\n".join(LotNotFound)))
        _logger.error('----------------------------------------------------------------------------------------------------------------------------')