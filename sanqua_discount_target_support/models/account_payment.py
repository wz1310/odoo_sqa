from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class AccountPayment(models.Model):
    _inherit = "account.payment"


    customer_discount_id = fields.Many2one('discount.target.support.customer', required=False, string="Customer Discount")
    remaining_disc_amount = fields.Monetary(string="Remaining Discount", compute="_compute_remaining_disc", store=True)
    settlement_request_id = fields.Many2one('settlement.request','Settlement Request')

    @api.depends('customer_discount_id')
    def _compute_remaining_disc(self):
        for rec in self:
            res = 0
            if rec.customer_discount_id.id:
                res = rec.customer_discount_id.remain_disc
            rec.remaining_disc_amount = res

    # @api.onchange('journal_id')
    # def onchange_journal_id(self):
    #     context = self.env.context
    #     move_id = self.env[context.get('active_model')].browse(context.get('active_id'))
    #     return {'domain':{'customer_discount_id':[('partner_id','=',move_id.partner_id.id),('state','=','approved')]}}

    @api.onchange('amount')
    def _onchange_(self):
        if self.customer_discount_id:
            if self.amount > self.remaining_disc_amount:
                raise UserError(_("You have not enough remaining discount to pay this amount!"))

    def post(self):
        for rec in self:
            if rec.customer_discount_id:
                if rec.amount > rec.remaining_disc_amount:
                    raise UserError(_("You have not enough remaining discount to pay this amount!"))
            res = super(AccountPayment, rec).post()
            if res == True:
                rec.env['discount.target.support.customer.usage'].create({
                    'disc_customer_id':rec.customer_discount_id.id,
                    'payment_id':rec.id,
                    'disc_usage':rec.amount,
                    'invoice_id': rec.invoice_ids.ids[0] if rec.invoice_ids else False,
                    'settlement_request_number' : self.settlement_request_id.name,
                    'settlement_request_date': self.settlement_request_id.request_date
                })
        return res