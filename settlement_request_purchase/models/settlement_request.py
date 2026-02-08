from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SettlementRequest(models.Model):
    _inherit = 'settlement.request'

    invoice_type = fields.Selection([
        ('out_invoice', 'Invoice'),
        ('in_invoice', 'Bills'),
    ], string='Type',readonly=True,track_visibility=True)
    total_pay_amount = fields.Monetary(string='Total',compute='compute_get_pay_amount_total')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')

    def submit_register_payment(self):
        for line in self.line_ids:
            payment_id = self.env['account.payment'].create({
                'payment_method_id': self.env.ref("account.account_payment_method_manual_in").id,
                'payment_type': 'inbound' if self.invoice_type=='out_invoice' else 'outbound',
                'payment_date': line.date,
                'partner_id':line.partner_id.id,
                'invoice_ids': [(6, False, line.invoice_id.ids)],
                'amount': line.pay_amount,
                'journal_id': line.journal_id.id,
                'partner_type': 'customer' if self.invoice_type=='out_invoice' else 'supplier',
                'customer_discount_id': line.discount_id.id,
                'settlement_request_id': self.id,
            })
            payment_id.post()
            line.payment_id = payment_id

    @api.depends('line_ids.pay_amount')
    def compute_get_pay_amount_total(self):
        for rec in self:
            if rec.line_ids:
                rec.total_pay_amount = sum([line.pay_amount for line in rec.line_ids])
            else:
                rec.total_pay_amount = 0.0


    def _return_domain(self):
        if self.invoice_type == 'out_invoice':
            return {'domain':{'partner_id':[('customer','=',True)]}}
        else:
            return {'domain':{'partner_id':[('supplier','=',True)]}}

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        return self._return_domain()

    @api.onchange('invoice_type')
    def _onchange_invoice_type(self):
        return self._return_domain()

class SettlementRequestLine(models.Model):
    _inherit = 'settlement.request.line'

    invoice_type = fields.Selection(related="settlement_id.invoice_type", string='Type',readonly=True,track_visibility=True)