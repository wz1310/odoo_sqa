# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp

class QualityWizard(models.TransientModel):
    _name = 'quality.wizard'
    _description = 'quality wizard'

    @api.model
    def default_get(self, fields):
        res = super(QualityWizard, self).default_get(fields)
        if self._context and self._context.get('active_id') and self._context.get('active_model'):
            if self._context.get('active_model') == 'stock.move':
                move = self.env['stock.move'].browse(self._context['active_id'])
                if move.pass_qty:
                    res['pass_qty'] = move.pass_qty
                if move.fail_qty:
                    res['fail_qty'] = move.fail_qty
                if move.fail_reason:
                    res['fail_reason'] = move.fail_reason
                if 'picking_id' in fields:
                    res['picking_id'] = move.id
                if 'product_id' in fields:
                    res['product_id'] = move.product_id.id
                if 'product_uom_id' in fields:
                    res['product_uom_id'] = move.product_uom.id
                if 'product_qty' in fields:
                    res['product_qty'] = move.quantity_done
                list_ids = []
                for line in move.move_line_nosuggest_ids:
                    vals = ((0, 0, {
                        'move_line_id': line.id,
                        'lot_id': line.lot_id.id,
                        'lot_name' : line.lot_name,
                        'qty_done': line.qty_done,
                        'fail_qty': line.fail_qty or 0.0,
                    }))
                    list_ids.append(vals)
                if list_ids:
                    res['quality_line_ids'] = list_ids
        return res

    @api.onchange('pass_qty')
    def onchange_qc(self):
        tt_qty = self.pass_qty + self.fail_qty
        if self.pass_qty and self.fail_qty and self.product_qty < tt_qty:
            raise UserError(_('Sum of Pass and Quarantine Qty Should be equal to the Product Qty.'))
        if self.pass_qty and self.pass_qty > self.product_qty:
            raise UserError(_('Pass Qty Should not be greater than Product Qty.'))
        if self.fail_qty and self.fail_qty > self.product_qty:
            raise UserError(_('Quarantine Qty Should not be greater than Product Qty.'))

    
    def do_quality_check(self):
        if self._context and self._context.get('active_id') and self._context.get('active_model'):
            stock_total = 0
            if self._context.get('active_model') == 'stock.move':
                move = self.env['stock.move'].browse(self._context['active_id'])
                move.pass_qty = self.pass_qty
                move.fail_qty = self.fail_qty
                move.fail_reason = self.fail_reason
                stock_total = move.pass_qty + move.fail_qty
                if stock_total != move.quantity_done:
                    raise UserError(_('Sum of Pass and Quarantine Qty '
                                      'should be equal to the Product Qty.'))
                for line in self.quality_line_ids:
                    if line.fail_qty > 0:
                        line.move_line_id.write({'fail_qty': line.fail_qty,
                                                 'is_fail': True})
                    else:
                        line.move_line_id.write({'fail_qty': 0.0,
                                                 'is_fail': False})
        return True

    picking_id = fields.Many2one('stock.move', 'Stock Picking')
    product_id = fields.Many2one('product.product', 'Product')
    product_qty = fields.Float(string='Quantity', required=True,
                               digits=dp.get_precision('Product Unit of Measure'))
    product_uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    pass_qty = fields.Float(string="Pass Qty", digits=dp.get_precision('Product Unit of Measure'))
    fail_qty = fields.Float(string="Quarantine Qty", digits=dp.get_precision('Product Unit of Measure'), compute='_compute_fail_qty')
    fail_qty_fake = fields.Float(string="Quarantine Qty", digits=dp.get_precision('Product Unit of Measure'), related="fail_qty")
    fail_reason = fields.Char(string="Quarantine Reason")
    quality_line_ids = fields.One2many('quality.wizard.line', 'quality_id')
    reason_qc_picking_id = fields.Many2one(
        'master.reason.qc.picking', 'Quarantine Reason')
    notes_qc_picking = fields.Text('Notes')
    
    @api.onchange('reason_qc_picking_id')
    def onchange_reason_qc_picking_id(self):
        if self.reason_qc_picking_id:
            self.fail_reason = self.reason_qc_picking_id.name

    @api.depends('quality_line_ids.fail_qty')
    def _compute_fail_qty(self):
        """ compute fail qty """
        amount = 0.0
        for line in self.quality_line_ids:
            amount += line.fail_qty
#         if amount > self.pass_qty:
#             raise UserError(_('Quarantine Qty Should not be greater than Pass Qty.'))
        self.fail_qty = amount

class QualityWizardLine(models.TransientModel):
    _name = 'quality.wizard.line'
    _description = 'quality wizard line'

    quality_id = fields.Many2one('quality.wizard')
    move_line_id = fields.Many2one('stock.move.line', 'Stock Move Line', index=True)
    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial Number')
    lot_name = fields.Char('Lot Name')
    qty_done = fields.Float(default=0.0, digits=dp.get_precision('Product Unit of Measure'))
    fail_qty = fields.Float(string="Quarantine Qty",
                            digits=dp.get_precision('Product Unit of Measure'))

    @api.onchange('fail_qty')
    def onchange_fail_qty(self):
        """ onchange fail quantity """
        if self.fail_qty > self.qty_done:
            raise UserError(_('Quarantine quantity should not greater than initial quantity.'))
        elif self.fail_qty < 0:
            raise UserError(_('Quarantine quantity should not a negative value.'))
