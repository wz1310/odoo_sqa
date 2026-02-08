# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp

class QualityWizard(models.TransientModel):
    _inherit = 'quality.wizard'

    @api.model
    def default_get(self, fields):
        res = super(QualityWizard, self).default_get(fields)
        if self._context and self._context.get('active_id') and self._context.get('active_model'):
            if self._context.get('active_model') == 'stock.move':
                move = self.env['stock.move'].browse(self._context['active_id'])
                if move.qc_production_id:
                    res['qc_production_id'] = move.qc_production_id.id
                if move.reason_qc_id:
                    res['reason_qc_id'] = move.reason_qc_id.id
                if move.notes_qc:
                    res['notes_qc'] = move.notes_qc
        return res

    qc_production_id = fields.Many2one(
        'mrp.production', 'Manufacturing Order', readonly=True)
    reason_qc_id = fields.Many2one(
        'master.reason.qc', 'Quarantine Reason QC')
    notes_qc = fields.Text('Notes')

    @api.onchange('reason_qc_id')
    def onchange_reason_qc_id(self):
        if self.reason_qc_id:
            self.fail_reason = self.reason_qc_id.name

    def do_quality_check(self):
        res = super(QualityWizard, self).do_quality_check()
        move = self.picking_id
        if not move and self._context and self._context.get('active_id') and \
            self._context.get('active_model'):
            if self._context.get('active_model') == 'stock.move':
                move = self.env['stock.move'].browse(self._context['active_id'])
        if move:
            values = {}
            if self.reason_qc_id:
                values['reason_qc_id'] = self.reason_qc_id.id
            if self.notes_qc:
                values['notes_qc'] = self.notes_qc
            if values:
                move.write(values)
        return res
