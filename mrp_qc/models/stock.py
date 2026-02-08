"""File Stock"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class StockLocation(models.Model):
    """class inherit stock.location"""
    _inherit = 'stock.location'

    location_qc_for_manufacture = fields.Boolean('QC location for Manufacture',
        help="Set QC location for manufacture")

class StockPickingType(models.Model):
    """class inherit stock.picking.type"""
    _inherit = 'stock.picking.type'

    finished_location_qc_id = fields.Many2one(
        'stock.location', 'Finished Location after QC',
        check_company=True,
        help="Set the Finisihed Location after QC the products")

class StockPicking(models.Model):
    """class inherit stock.picking"""
    _inherit = 'stock.picking'

    finished_picking_qc = fields.Boolean(
        'Finished Picking QC',
        help="Flag of Last Picking of QC process")

    def action_done(self):
        """ override action_done function """
        res = super(StockPicking, self).action_done()
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        if self.finished_picking_qc:
            for line in self.move_lines:
                if line.fail_qty:
                    self.rejected_moves(line, context=None)
                total_qty = line.pass_qty + line.fail_qty
                #Change by ADI - 2021-05-19 ---> line.product_uom_qty > 0
                if line.quantity_done <= 0 and line.product_uom_qty > 0:
                    raise UserError(
                        _('Done Quantity should be filled in ( ' \
                            + (line.product_id.default_code or '') \
                            + ' ' + (line.product_id.name) + ' )'))
                if not total_qty == round(line.quantity_done, precision):
                    raise UserError(
                        _('Sum of Pass and Quarantine Qty Should be equal to Done Qty in ( ' \
                            + (line.product_id.default_code or '') \
                            + ' ' + (line.product_id.name) + ' )'))
                if line.fail_qty and not line.fail_reason:
                    raise UserError(
                        _('There is a quarantine qty in (' + (line.product_id.default_code or '') \
                            + ' ' + (line.product_id.name) \
                            + ') .So Kindly give a quarantine reason.'))
                qc_obj = self.env['stock.quality.check']
                if not line.pass_qty and line.fail_qty:
                    qc_state = 'failed'
                elif line.pass_qty and not line.fail_qty:
                    qc_state = 'passed'
                elif line.pass_qty and line.fail_qty:
                    qc_state = 'partial'
                if line.quantity_done:
                    create_vals = {
                        'product_id': line.product_id.id,
                        'done_qty': line.quantity_done,
                        'pass_qty': line.pass_qty,
                        'fail_qty': line.fail_qty,
                        'product_uom_id': line.product_uom.id,
                        'state': qc_state,
                        'date': fields.Date.today(),
                        'move_id': line.id,
                        'reason_of_failure': line.fail_reason,
                    }
                    new_check_id = qc_obj.create(create_vals)
                    if new_check_id:
                        line.write({'check_id': new_check_id.id})
        return res

class StockMove(models.Model):
    """class inherit stock.move"""
    _inherit = 'stock.move'

    qc_production_id = fields.Many2one(
        'mrp.production', 'QC Production Order for finished products', check_company=True)
    finished_picking_qc = fields.Boolean(
        'Finished Picking QC', related='picking_id.finished_picking_qc',
        help="Flag of Last Picking of QC process")
    reason_qc_id = fields.Many2one(
        'master.reason.qc', 'Quarantine Reason QC')
    notes_qc = fields.Text('Notes QC')

    def _action_done(self, cancel_backorder=False):
        res = super(StockMove, self)._action_done(cancel_backorder=cancel_backorder)
        moves = self.exists().filtered(lambda x: x.qc_production_id)
        if moves:
            qc_production_ids = moves.mapped('qc_production_id')
            for qcp in qc_production_ids:
                product_ids = qcp.move_finished_ids.mapped('product_id')
                for product in product_ids:
                    fmoves = qcp.move_finished_ids.filtered(
                        lambda mv: mv.state == 'done' and mv.product_id.id == product.id)
                    finish_qty = 0.0
                    product_uom = False
                    for fm in fmoves:
                        if not product_uom:
                            finish_qty += fm.quantity_done
                            product_uom = fm.product_uom
                        elif product_uom and product_uom.id != fm.product_uom.id:
                            finish_qty += fm.product_uom._compute_quantity(
                                fm.quantity_done, product_uom, round=False)
                        else:
                            finish_qty += fm.quantity_done
                    qc_qty = 0.0
                    for m in qcp.qc_move_finished_ids.filtered(
                        lambda qmf: qmf.product_id.id == product.id):
                        qty = 0.0
                        if m.state in ['done', 'cancel'] and m.quantity_done <= 0:
                            qty += m.quantity_done
                        else:
                            qty += m.product_uom_qty
                        if not product_uom:
                            qc_qty += qty
                            product_uom = m.product_uom
                        elif product_uom and product_uom.id != m.product_uom.id:
                            qc_qty += m.product_uom._compute_quantity(
                                qty, product_uom, round=False)
                        else:
                            qc_qty += qty
                    if finish_qty < qty:
                        raise UserError(
                            _('Quantity in QC process more than result of Manufacturing Order.\n'\
                              'Please check again, quantity product ('+product.display_name+')'))
        return res
