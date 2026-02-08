from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    ctx_currency_id = fields.Many2one('res.currency', string='Currency',compute='_compute_ctx_amount')
    ctx_amount_total = fields.Monetary(compute='_compute_ctx_amount_total', string='Total')
    
    @api.depends_context('activity_id')
    def _compute_ctx_amount_total(self):
        for rec in self:
            activity_id = rec._context.get('params')
            if activity_id:
                activity_id = activity_id.get('id')
            payment_ids = self.env['collection.activity.line.payment'].search([('activity_id','=',activity_id), ('journal_id','=',rec.id)])
            rec.ctx_amount_total = sum([payment.amount for payment in payment_ids])
            rec.ctx_currency_id = self.env.user.company_id.currency_id