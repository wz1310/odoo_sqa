from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    settlement_ids = fields.Many2many('settlement.request.line', string='Settlement')
    #FIXME: Store field in server
    # amount_settlement_residual = fields.Monetary(string='Residual Settlement',compute='_compute_calculate_amount_settlement_residual',store=True)
    amount_settlement_residual = fields.Monetary(string='Residual Settlement',compute='_compute_calculate_amount_settlement_residual')

    @api.depends('settlement_ids')
    def _compute_calculate_amount_settlement_residual(self):
        for rec in self:
            res = rec.credit
            submitted_settlement = rec.settlement_ids.filtered(lambda r: r.settlement_id.state != 'draft')
            if submitted_settlement:
                total = sum([x.pay_amount for x in submitted_settlement])
                res = rec.credit - total
            rec.amount_settlement_residual = res