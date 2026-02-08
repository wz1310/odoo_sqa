# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError,RedirectWarning,AccessError
from datetime import datetime, timedelta, date
import calendar

class AccMoveLineInherrits(models.Model):
    _inherit = 'account.move.line'
    picking_id = fields.Many2one('stock.picking')

class AccMoveInherrits(models.Model):
    _inherit = 'account.move'
    analytic_account_gbl = fields.Many2one('account.analytic.account', 'Analytic Account',track_visibility='onchange')

    @api.onchange('analytic_account_gbl')
    def _onchange_acg(self):
        if self.analytic_account_gbl:
            for x in self.invoice_line_ids:
                x.analytic_account_id = self.analytic_account_gbl.id
                if x.analytic_account_id:
                    for y in self.line_ids:
                        y.analytic_account_id = x.analytic_account_id
        else:
            for x in self.invoice_line_ids:
                x.analytic_account_id = False

    def button_draft(self):
        res = super(AccMoveInherrits, self).button_draft()
        find_commercil = self.env['etax.invoice.merge'].search([('invoice_ids','=',self.id),('state','=','posted')])
        if find_commercil.name:
            raise UserError(_('You cannot reset to draft an entry having a posted Invoice commercial %s')% find_commercil.name)
        return res

    def _depreciate(self):
        for move in self.filtered(lambda m: m.asset_id):
            asset = move.asset_id
            if asset.state in ('open', 'pause'):
                asset.value_residual -= abs(sum(move.line_ids.filtered(lambda l: l.account_id == asset.account_depreciation_id).mapped('balance')))
            elif asset.state == 'close':
                asset.value_residual -= abs(sum(move.line_ids.filtered(lambda l: l.account_id != asset.account_depreciation_id).mapped('balance')))
            else:
                raise UserError(_('You cannot post a depreciation on an asset : %s') % asset.name)

    @api.model
    def _autopost_draft_entries(self):
        cron = self.env.ref('account.ir_cron_auto_post_draft_entry')
        now = fields.Datetime.context_timestamp(self, datetime.now())
        last_d = now.replace(day = calendar.monthrange(now.year, now.month)[1]).date()
        p_start_time = False
        if fields.Date.today() == last_d:
            try:
                p_start_time = fields.Datetime.now()
                records = self.search([
                    ('state', '=', 'draft'),
                    ('date', '<=', fields.Date.today()),
                    ('auto_post', '=', True),
                    ], limit=500)
                records.post()
            except Exception as e:
                self.env['log.post.asset'].create({
                    'start_time':p_start_time,
                    'end_time':fields.Datetime.now(),
                    'logs':e
                    })
        else:
            print("Execution date for posting asset account is not today")