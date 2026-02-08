"""File MRP"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    """class inherit mrp.production"""
    _inherit = 'mrp.production'

    finished_location_qc_id = fields.Many2one(
        'stock.location', 'Finished Location after QC',
        check_company=True,
        help="Set the Finisihed Location after QC the products")
    state = fields.Selection(selection_add=[('waiting_qc', 'Waiting QC'), ('qc_done', 'QC Done')])
    qc_move_finished_ids = fields.One2many(
        'stock.move', 'qc_production_id', 'QC Finished Products',
        copy=False, states={'waiting_qc': [('readonly', True)], 'qc_done': [('readonly', True)]},
        domain=[('scrapped', '=', False)])

    @api.depends('move_raw_ids.state', 'move_finished_ids.state', 'workorder_ids',
                 'workorder_ids.state', 'qty_produced', 'move_raw_ids.quantity_done',
                 'product_qty', 'finished_location_qc_id', 'qc_move_finished_ids.state')
    def _compute_state(self):
        """ Compute the production state. It use the same process than stock
        picking. It exists 3 extra steps for production:
        - planned: Workorder has been launched (workorders only)
        - progress: At least one item is produced.
        - to_close: The quantity produced is greater than the quantity to
        produce and all work orders has been finished.
        """
        # TODO: duplicated code with stock_picking.py
        for production in self:
            if not production.move_raw_ids:
                production.state = 'draft'
            elif all(move.state == 'draft' for move in production.move_raw_ids):
                production.state = 'draft'
            elif all(move.state == 'cancel' for move in production.move_raw_ids):
                production.state = 'cancel'
            elif all(move.state in ['cancel', 'done'] for move in production.move_raw_ids):
                if production.qc_move_finished_ids:
                    if all(qc.state in ['cancel', 'done'] for qc in production.qc_move_finished_ids):
                        production.state = 'qc_done'
                    else:
                        production.state = 'waiting_qc'
                else:
                    production.state = 'done'
            elif production.move_finished_ids.filtered(lambda m: m.state not in ('cancel', 'done') and m.product_id.id == production.product_id.id)\
                 and (production.qty_produced >= production.product_qty)\
                 and (not production.routing_id or all(wo_state in ('cancel', 'done') for wo_state in production.workorder_ids.mapped('state'))):
                production.state = 'to_close'
            elif production.workorder_ids and any(wo_state in ('progress') for wo_state in production.workorder_ids.mapped('state'))\
                 or production.qty_produced > 0 and production.qty_produced < production.product_uom_qty:
                production.state = 'progress'
            elif production.workorder_ids:
                production.state = 'planned'
            else:
                production.state = 'confirmed'

            # Compute reservation state
            # State where the reservation does not matter.
            if production.state in ('draft', 'done', 'cancel', 'qc_done', 'waiting_qc'):
                production.reservation_state = False
            # Compute reservation state according to its component's moves.
            else:
                relevant_move_state = production.move_raw_ids._get_relevant_state_among_moves()
                if relevant_move_state == 'partially_available':
                    if production.routing_id and production.routing_id.operation_ids and production.bom_id.ready_to_produce == 'asap':
                        production.reservation_state = production._get_ready_to_produce_state()
                    else:
                        production.reservation_state = 'confirmed'
                elif relevant_move_state != 'draft':
                    production.reservation_state = relevant_move_state

    @api.depends('move_raw_ids', 'is_locked', 'state', 'move_raw_ids.quantity_done')
    def _compute_unreserve_visible(self):
        for order in self:
            already_reserved = order.is_locked and order.state not in (
                'done', 'cancel', 'waiting_qc', 'qc_done') and order.mapped(
                    'move_raw_ids.move_line_ids')
            any_quantity_done = any([m.quantity_done > 0 for m in order.move_raw_ids])
            order.unreserve_visible = not any_quantity_done and already_reserved

    def unlink(self):
        if any(production.state in ['waiting_qc', 'qc_done'] for production in self):
            raise UserError(_('Cannot delete a manufacturing order in QC Process.'))
        return super(MrpProduction, self).unlink()

    @api.onchange('picking_type_id')
    def onchange_picking_type(self):
        super(MrpProduction, self).onchange_picking_type()
        if self.picking_type_id.finished_location_qc_id:
            self.finished_location_qc_id = self.picking_type_id.finished_location_qc_id.id

    def _get_qc_finish_move_value(self, product_id, product_uom_qty, product_uom,
                                  picking_type_id, location_id, location_dest_id):
        return {
            'product_id': product_id,
            'product_uom_qty': product_uom_qty,
            'product_uom': product_uom,
            'name': self.name,
            'date': fields.Date.today(),
            'date_expected': self.date_planned_finished,
            'picking_type_id': picking_type_id,
            'location_id': location_id.id,
            'location_dest_id': location_dest_id.id,
            'company_id': self.company_id.id,
            'qc_production_id': self.id,
            'warehouse_id': location_dest_id.get_warehouse().id,
            'origin': self.name,
            'group_id': self.procurement_group_id.id,
            'propagate_cancel': self.propagate_cancel,
            'propagate_date': self.propagate_date,
            'propagate_date_minimum_delta': self.propagate_date_minimum_delta,
        }

    def button_qc_confirm(self):
        self.ensure_one()
        self._check_company()
        self._check_lots()

        print(' ============== START ACTION ON BUTTON button_qc_confirm ============== ')
        _logger.info(' ============== START ACTION ON BUTTON button_qc_confirm ============== ')
        _logger.info('>>> MO No. ' + str(self.name))

        # 1. Print self.finished_location_qc_id
        _logger.info('#1 self.finished_location_qc_id : ' + str(self.finished_location_qc_id))
        print('#1 self.finished_location_qc_id : ' + str(self.finished_location_qc_id))

        if self.finished_location_qc_id:
            warehouse = self.finished_location_qc_id.get_warehouse()
            _logger.info('#2. Warehouse : ' + str(warehouse))
            print('#2. Warehouse : ' + str(warehouse))

            if not warehouse:
                warehouse = self.env['stock.warehouse'].search(
                    [('company_id', '=', self.company_id.id)], limit=1)
                _logger.info('#3. Not Warehouse, Warehouse :' + str(warehouse))
                print('#3. Not Warehouse, Warehouse :' + str(warehouse))

            if not warehouse or not warehouse.int_type_id:
                raise UserError(_('Cannot find Internal Transfer Picking Type.'))
            qc_locations = self.env['stock.location'].search([
                ('location_qc_for_manufacture', '=', True), ('usage', '=', 'internal'),
                ('company_id', '=', self.company_id.id)], limit =1)
            _logger.info('#4. qc_locations : ' + str(qc_locations))
            print('#4. qc_locations : ' + str(qc_locations))

            qc_location = False
            for qc_loc in qc_locations:
                qc_warehouse = qc_loc.get_warehouse()
                # if qc_warehouse and qc_warehouse.id == warehouse.id:
                qc_location = qc_loc
                break

            _logger.info('#5. qc_location : ' + str(qc_location))
            print('#5. qc_location : ' + str(qc_location))
            if not qc_location:
                raise UserError(_('Cannot find QC Location.'))

            product_ids = self.move_finished_ids.mapped('product_id')
            _logger.info('#6. product_ids : ' + str(product_ids))
            print('#6. product_ids : ' + str(product_ids))

            for product in product_ids:
                qc_moves = False
                moves = self.move_finished_ids.filtered(lambda m: m.state == 'done' and \
                                                        m.product_id.id == product.id)
                _logger.info('#7. moves : ' + str(moves))                                                        
                print('#7. moves : ' + str(moves))

                qc_qty = 0.0
                product_uom = False
                lot_list = []
                lot_data = {}
                for move in moves:
                    if not product_uom:
                        qc_qty += move.quantity_done
                        product_uom = move.product_uom
                        print('#8.1 not product_uom : ')
                        print('#qc_qty : ' + str(qc_qty))
                        print('#product_uom : ' + str(product_uom))

                        _logger.info('#8.1 not product_uom : ')
                        _logger.info('#qc_qty : ' + str(qc_qty))
                        _logger.info('#product_uom : ' + str(product_uom))
                    elif product_uom and product_uom.id != move.product_uom.id:
                        qc_qty += move.product_uom._compute_quantity(
                            move.quantity_done, product_uom, round=False)
                        print('#8.2 not product_uom : ')
                        print('#qc_qty : ' + str(qc_qty))
                        print('#product_uom : ' + str(product_uom))

                        _logger.info('#8.2 not product_uom : ')
                        _logger.info('#qc_qty : ' + str(qc_qty))
                        _logger.info('#product_uom : ' + str(product_uom))
                    else:
                        qc_qty += move.quantity_done
                        print('#8.3 not product_uom : ')
                        print('#qc_qty : ' + str(qc_qty))
                        print('#product_uom : ' + str(product_uom))

                        _logger.info('#8.3 not product_uom : ')
                        _logger.info('#qc_qty : ' + str(qc_qty))
                        _logger.info('#product_uom : ' + str(product_uom))

                    move_lines = move._get_move_lines()
                    print('#9. move_lines : ' + str(move_lines))
                    _logger.info('#9. move_lines : ' + str(move_lines))

                    for ml in move_lines:
                        if ml.lot_id and ml.product_uom_id:
                            print('#10. ml.lot_id :' + str(ml.lot_id) + ' | ml.product_uom_id : ' + str(ml.product_uom_id))
                            _logger.info('#10.1 ml.lot_id :' + str(ml.lot_id) + ' | ml.product_uom_id : ' + str(ml.product_uom_id))
                            _logger.info('#10.2 Lot No : ' + str(ml.lot_id.name))

                            line_qty = ml.product_uom_id._compute_quantity(
                                ml.qty_done, product_uom, round=False)

                            print('#11. line_qty : ' + str(line_qty) + '| qty_done : ' + str(ml.qty_done))
                            _logger.info('#11. line_qty : ' + str(line_qty) + '| qty_done : ' + str(ml.qty_done))

                            if ml.lot_id.id not in lot_data:
                                lot_list.append(ml.lot_id.id)
                                lot_data[ml.lot_id.id] = line_qty
                            else:
                                lot_data[ml.lot_id.id] += line_qty

                    print( '#12. lot_list : ' + str(lot_list) + '| lot_data : ' + str(lot_data) )
                    _logger.info( '#12. lot_list : ' + str(lot_list) + '| lot_data : ' + str(lot_data) )  

                #QC Moves
                qc_moves_values = self._get_qc_finish_move_value(
                    product.id, qc_qty, product_uom.id, warehouse.int_type_id.id,
                    self.location_dest_id, qc_location)
                print('#13. qc_moves_values : ' + str(qc_moves_values))
                _logger.info('#13. qc_moves_values : ' + str(qc_moves_values))

                qc_moves = self.env['stock.move'].create(qc_moves_values)
                print('#14. qc_moves : ' + str(qc_moves))
                _logger.info('#14. qc_moves : ' + str(qc_moves))

                qc_moves._action_confirm()
                #Finish QC Moves
                finish_moves_values = self._get_qc_finish_move_value(
                    product.id, qc_qty, product_uom.id, warehouse.int_type_id.id,
                    qc_location, self.finished_location_qc_id)
                print('#15. finish_moves_values : ' + str(finish_moves_values))
                _logger.info('#15. finish_moves_values : ' + str(finish_moves_values))
                
                finish_moves = self.env['stock.move'].create(finish_moves_values)
                print('#16. finish_moves : ' + str(finish_moves))
                _logger.info('#16. finish_moves : ' + str(finish_moves))                

                qc_moves.write({'move_dest_ids': [(4, finish_moves.id)]})
                print('#17. finish_moves : ' + str(qc_moves.move_dest_ids))
                _logger.info('#17. finish_moves : ' + str(qc_moves.move_dest_ids))              
                

                finish_moves._action_confirm()

                if finish_moves.picking_id:
                    finish_moves.picking_id.write({'finished_picking_qc':True})
                qc_moves._action_assign()
                finish_moves._action_assign()
                if lot_list and lot_data and len(qc_moves) == 1:
                    qc_move_qty = qc_qty
                    qc_move_lines = qc_moves._get_move_lines()

                    print('#18. qc_move_qty : ' + str(qc_move_qty))
                    print('#19. qc_move_lines : ' + str(qc_move_lines))

                    _logger.info('#18. qc_move_qty : ' + str(qc_move_qty))
                    _logger.info('#19. qc_move_lines : ' + str(qc_move_lines))

                    if qc_move_lines:
                        first_qc_move_line = qc_move_lines[0]
                        print('#20. first_qc_move_line : ' + str(first_qc_move_line))   
                        _logger.info('#20. first_qc_move_line : ' + str(first_qc_move_line))   

                        remove_qc_move_lines = qc_move_lines - first_qc_move_line
                        print('#21. remove_qc_move_lines : ' + str(remove_qc_move_lines))
                        _logger.info('#21. remove_qc_move_lines : ' + str(remove_qc_move_lines))

                        for qml in qc_move_lines:
                            if qml.lot_id and qml.lot_id.id in lot_data:
                                if lot_data[qml.lot_id.id] <= qc_move_qty:
                                    qml.product_uom_qty = lot_data[qml.lot_id.id]
                                    qml.qty_done = lot_data[qml.lot_id.id]
                                    qc_move_qty -= lot_data[qml.lot_id.id]
                                    print('#22.1 qml.product_uom_qty : ' + str(qml.product_uom_qty) + '| qml.qty_done : ' + str(qml.product_uom_qty) + ' | qc_move_qty : ' + str(qc_move_qty) )
                                    _logger.info('#22.1 qml.product_uom_qty : ' + str(qml.product_uom_qty) + '| qml.qty_done : ' + str(qml.product_uom_qty) + ' | qc_move_qty : ' + str(qc_move_qty) )
                                    _logger.info('#22.2.1 qml.lot_id.name : ' + str(qml.lot_id.name) )
                                else:
                                    qml.product_uom_qty = qc_move_qty
                                    qml.qty_done = qc_move_qty
                                    qc_move_qty -= qc_move_qty
                                    print('#22.2 qml.product_uom_qty : ' + str(qml.product_uom_qty) + '| qml.qty_done : ' + str(qml.product_uom_qty) + ' | qc_move_qty : ' + str(qc_move_qty) )
                                    _logger.info('#22.2 qml.product_uom_qty : ' + str(qml.product_uom_qty) + '| qml.qty_done : ' + str(qml.product_uom_qty) + ' | qc_move_qty : ' + str(qc_move_qty) )
                                    _logger.info('#22.2.2 qml.lot_id.name : ' + str(qml.lot_id.name) )
                                lot_list.remove(qml.lot_id.id)
                        for rec_remove in remove_qc_move_lines:
                            print('#23. rec_remove.unlink()')
                            _logger.info('#23. rec_remove.unlink()')
                            rec_remove.unlink()
                        if qc_move_qty > 0.0 and first_qc_move_line:
                            print('#24. qc_move_qty : ' + str(qc_move_qty))
                            _logger.info('#24. qc_move_qty : ' + str(qc_move_qty))
                            already_change = False
                            for lot in lot_list:
                                print('#25. lot : ' + str(lot))
                                print('#26. lot_data : ' + str(lot_data))
                                print('#27. qc_move_qty : ' + str(qc_move_qty))

                                _logger.info('#25. lot : ' + str(lot))
                                _logger.info('#26. lot_data : ' + str(lot_data))
                                _logger.info('#27. qc_move_qty : ' + str(qc_move_qty))
                                if lot in lot_data and lot_data[lot] <= qc_move_qty:
                                    if already_change:
                                        first_qc_move_line.copy(
                                            default={'lot_id': lot,
                                                     'product_uom_qty': lot_data[lot],
                                                     'qty_done': lot_data[lot]})
                                    else:
                                        first_qc_move_line.write(
                                            {'lot_id': lot,
                                             'product_uom_qty': lot_data[lot],
                                             'qty_done': lot_data[lot]})
                                        already_change = True
                                    qc_move_qty -= lot_data[lot]
                                if qc_move_qty <= 0.0:
                                    break
        else:
            raise UserError(_('Picking Type dont have Finished Location after QC'))
        return True
