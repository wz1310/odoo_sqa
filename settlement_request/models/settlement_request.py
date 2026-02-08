# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError

import logging
_logger = logging.getLogger(__name__)

class SettlementRequest(models.Model):
    _name = 'settlement.request'
    _description = 'Settlement Request'
    _inherit = ["approval.matrix.mixin",'mail.thread', 'mail.activity.mixin']

    company_id = fields.Many2one('res.company', string='Company',default=lambda self: self.env.company.id,track_visibility='onchange')
    name = fields.Char(string='Name',track_visibility='onchange')
    activity_id = fields.Many2one('collection.activity', string='Collection',track_visibility='onchange')
    request_date = fields.Date(string='Request Date',track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', string='Customer',track_visibility='onchange')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancel', 'Cancelled'),
        ('done', 'Done')
    ], string='State',default='draft',track_visibility='onchange')
    line_ids = fields.One2many('settlement.request.line', 'settlement_id', string='Invoices',track_visibility='onchange')

    _constraints = [
        ('name_unique', 'unique (name)', 'Name must be unique'),
    ]

    
    def _fetch_next_seq(self):
        return self.env['ir.sequence'].next_by_code('seq.settlement.request')

    @api.model_create_multi
    def create(self, vals):

        for val in vals:
            if val.get('name') == False or val.get('name').lower() == 'new':
                val.update({'name':self._fetch_next_seq()})
        return super().create(vals)

    # def unlink(self):
    #     if self.env.user.has_group('settlement_request.group_settlement_approver') :
    #             raise UserError(_("You don't have access to delete this document."))
    #     return super.unlink()

    @api.onchange('activity_id','partner_id')
    def _onchange_activity_partner(self):
        if self.activity_id:
            line_ids = [(5,0,0)]
            collection_payment_ids = self.env['collection.activity.line.payment'].search([('activity_id','=',self.activity_id.id),('partner_id','=',self.partner_id.id)])
            for line in collection_payment_ids:
                data ={
                    'settlement_id':self.id,
                    'line_payment_id': line.id,
                    'invoice_id': line.line_id.invoice_id.id,
                    'journal_id': line.journal_id.id,
                    'discount_id': line.discount_id.id,
                    'pay_amount': line.amount
                }
                line_ids.append((0,0,data))
            self.line_ids = line_ids
            partner_ids = [line.id for line in self.activity_id.line_ids.mapped('partner_id')]
            return {'domain':{'partner_id':[('id','in',partner_ids)]}}
        else:
            if len(self.line_ids):
                
                
                if any(self.line_ids.mapped(lambda r:r.invoice_id.partner_id.id != self.partner_id.id)):
                    self.line_ids = [(5,0)]
            return {'domain':{'partner_id':[('customer','=',True)]}}
    
    def reset_follower_and_approvals(self):
        for rec in self:
            followers_partner = []
            for approval in rec.approval_ids:
                for approver in approval.approver_ids:
                    followers_partner.append(approver.partner_id.id)
            rec.message_unsubscribe(partner_ids=followers_partner)
            rec.approval_ids = [(5, 0)]

    def btn_draft(self):
        self.ensure_one()
        self.reset_follower_and_approvals()
        self.state = 'draft'

    def btn_submit(self):
        self.ensure_one()
        
        if not len(self.line_ids):
            raise UserError(_("At least require 1 invoice to process!"))
        else:
            
            for each in self.line_ids:
                if not each.date:
                    raise UserError(_('Please set payment date on each (%s).') % (each.invoice_id.display_name,))

                if each.discount_id:
                    if each.pay_amount > each.discount_id.remain_disc:
                        raise UserError(_("You have not enough remaining discount to pay this amount!"))
                
                if each.journal_entries_ids:
                    if each.pay_amount > each.journal_entries_total:
                        raise UserError(_("you cannot pay more than entries amount, please check again"))
                
                if each.pay_amount > each.amount_residual:
                    raise UserError(_("you cannot pay more than residual, please check again"))
                else:
                    residual = 0
                    balance = 0
                    if each.journal_id.name == 'Uang Muka Penjualan - Konsumen DO' or each.journal_id.name == 'Credit Note' or each.journal_id.name == 'Debit Note':
                        move_line_ids = self.env['account.move.line'].search([('partner_id','=',each.partner_id.id),('account_id','=',each.journal_id.default_debit_account_id.id)])
                        for record in move_line_ids:
                            if record.credit > 0:
                                if balance == 0:
                                    balance += record.credit
                                    residual = balance
                                else:
                                    balance = balance + record.credit
                                    residual = balance + record.credit
                            elif record.debit > 0:
                                if balance == 0:
                                    residual = residual - record.debit
                                    balance = balance - record.debit
                                else:
                                    balance = balance - record.debit
                                    residual = balance - record.debit
                        if each.pay_amount > balance:
                            raise UserError(_("Balance for %s for %s equals %s, please check again" % (each.journal_id.name,each.partner_id.name,balance,)))
                self.checking_approval_matrix(add_approver_as_follower=True, data={'state':'waiting_approval'})
            self.register_settlement_to_journal()

    def action_approve(self):
        for each in self.line_ids:
            if not each.date:
                raise UserError(_('Please set payment date on each (%s).') % (each.invoice_id.display_name,))

            if each.discount_id:
                if each.pay_amount > each.discount_id.remain_disc:
                    raise UserError(_("You have not enough remaining discount to pay this amount!"))
            
            if each.pay_amount > each.amount_residual:
                raise UserError(_("you cannot pay more than residual, please check again"))
        
        self.state = 'approved'
        for invoice in self.line_ids:
            invoice._post_invoice()

    def btn_approve(self):
        self.ensure_one()
        self.approving_matrix(post_action='action_approve')


    def submit_register_payment(self):
        for line in self.line_ids:
            payment_id = self.env['account.payment'].create({
                'payment_method_id': self.env.ref("account.account_payment_method_manual_in").id,
                'payment_type': 'inbound',
                'payment_date': line.date,
                'partner_id':line.partner_id.id,
                'invoice_ids': [(6, False, line.invoice_id.ids)],
                'amount': line.pay_amount,
                'journal_id': line.journal_id.id,
                'partner_type': 'customer',
                'customer_discount_id': line.discount_id.id,
                'settlement_request_id': self.id,
            })
            payment_id.post()
            line.payment_id = payment_id

    def btn_done(self):
        self.ensure_one()
        self.submit_register_payment()
        self.state = 'done'

    def register_settlement_to_journal(self):
        for rec in self.line_ids:
            for journal in rec.journal_entries_ids:
                journal.settlement_ids = [(4,rec.id)]

    def unregister_settlement_to_journal(self):
        for rec in self.line_ids:
            for journal in rec.journal_entries_ids:
                journal.settlement_ids = [(3,rec.id)]

    def action_reject(self):
        self.ensure_one()
        self.reset_follower_and_approvals()
        self.unregister_settlement_to_journal()
        self.state = 'rejected'

    def open_reject_message_wizard(self):
        self.ensure_one()
        
        form = self.env.ref('approval_matrix.message_post_wizard_form_view')
        context = dict(self.env.context or {})
        context.update({'default_prefix_message':"<h4>Rejecting Settlement Request</h4>","default_suffix_action": "action_reject"}) #uncomment if need append context
        context.update({'active_id':self.id,'active_ids':self.ids,'active_model':'settlement.request'})
        res = {
            'name': "%s - %s" % (_('Rejecting Settlement Request'), self.name),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'message.post.wizard',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res

    def btn_cancel(self):
        for invoice in self.line_ids:
            invoice.payment_id.action_draft()
            invoice.payment_id.unlink()
            invoice._unpost_invoice()
        self.unregister_settlement_to_journal()
        self.state = 'cancel'

class SettlementRequestLine(models.Model):
    _name = 'settlement.request.line'
    _description = 'Settlement Request Line'

    settlement_id = fields.Many2one('settlement.request', string='Settlement',required=True,track_visibility='onchange')
    partner_id = fields.Many2one(related='settlement_id.partner_id', string='Customer',track_visibility='onchange', store=True)
    line_payment_id = fields.Many2one('collection.activity.line.payment', string='Collection Payment Ref',track_visibility='onchange')
    invoice_id = fields.Many2one('account.move', string='Invoice',required=True,track_visibility='onchange')
    invoice_total = fields.Monetary(related='invoice_id.amount_total', string='Amount Invoice',track_visibility='onchange')
    currency_id = fields.Many2one(related='invoice_id.currency_id', string='Currency',track_visibility='onchange')
    journal_id = fields.Many2one('account.journal', string='Payment Method',required=True,track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company',default=lambda self: self.env.company.id,track_visibility='onchange')
    discount_id = fields.Many2one('discount.target.support.customer', string='Discounts',track_visibility='onchange')
    pay_amount = fields.Monetary(string='Pay Amount',track_visibility='onchange')
    amount_residual = fields.Monetary(compute='_compute_amount_residual', string='Amount Residual',track_visibility='onchange', stored=True)
    date = fields.Date(string='Date',track_visibility='onchange')
    divisi_id = fields.Many2one('crm.team', string='Division', related="invoice_id.team_id", store=True)
    account_id = fields.Many2one('account.account', related='journal_id.default_credit_account_id',string='Account')
    journal_entries_ids = fields.Many2many('account.move.line', string='Uang Muka')
    journal_entries_total = fields.Monetary(string='Amount Uang Muka',compute='calculate_journal_entries_total',track_visibility='onchange')
    is_down_payment = fields.Boolean(related='journal_id.is_down_payment',string='Is Down Payment?')
    payment_id = fields.Many2one('account.payment', string='Payment')

    _sql_constraints = [
        ('partner_id_invoice_id_settlement_id_unique', 'unique (invoice_id, settlement_id, journal_id)', 'Cannot choose different invoice from customer in collection.'),
    ]

    @api.onchange('line_payment_id')
    def _onchange_line_payment_id(self):
        if self.line_payment_id:
            self.update({
                'invoice_id':self.line_payment_id.line_id.invoice_id,
                'journal_id':self.line_payment_id.journal_id,
                'discount_id':self.line_payment_id.discount_id,
                'pay_amount':self.line_payment_id.amount
            })

    def _post_invoice(self):
        for rec in self:
            if rec.invoice_id.state == 'draft':
                print("start _post_invoice")
                rec.invoice_id.post()
                print("finish _post_invoice")

    def _unpost_invoice(self):
        for rec in self:
            rec.invoice_id.button_draft()
                
    @api.depends('invoice_id')
    def _compute_amount_residual(self):
        for rec in self:
            rec.amount_residual = rec.invoice_id.amount_residual

    @api.depends('journal_entries_ids')
    def calculate_journal_entries_total(self):
        for rec  in self:
            res = False
            if rec.journal_entries_ids:
                res = sum([x.amount_settlement_residual for x in rec.journal_entries_ids])
            rec.journal_entries_total = res
