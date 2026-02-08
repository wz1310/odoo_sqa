import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero

class InherietJournalPayment(models.Model):
    _name = 'inheriet.journal.payment'

    @api.model
    def _get_default_seq(self):
        return self.env["ir.sequence"].next_by_code("jurnal.payment.sequence")

    name = fields.Char(compute='com_name')
    seq = fields.Char(default=_get_default_seq)
    date = fields.Date(string="Date")
    vendor_code = fields.Char(string="Vendor Code")
    vendor_desc = fields.Text(string="Vendor Desc")
    remark = fields.Text(string="Remark")
    ref = fields.Char(string="Reference")
    account_id = fields.Many2one('account.account', string='Account')
    amount = fields.Float(string='Amount')
    amount_p = fields.Float(string='Amount')
    company_id = fields.Many2one('res.company',string='Company')
    sheet_id = fields.Integer()
    line_jp = fields.One2many('inheriet.journal.payment.sheet','jp_id',string="Payment sheet")
    id_ref_sheet = fields.Many2one('inheriet.journal.payment.child',domain="[('in_pay','=', True)]")
    id_jpss =fields.Char()
    id_exp = fields.Char()
    total_amount = fields.Float(compute='_compute_total_sum')
    cost_cnt = fields.Many2one('cost.center')
    cek_p = fields.Boolean(compute='cek_px')
    rem_am = fields.Float(string="Remain", compute='cek_rem')

    @api.depends('total_amount')
    def cek_rem(self):
        if self.total_amount != 0:
            self.rem_am = self.amount - self.total_amount
            self.amount_p = self.rem_am
        elif self.total_amount == 0:
            self.rem_am = 0
            self.cost_cnt = False
            self.amount_p = self.rem_am

    @api.depends('cek_p')
    def cek_px(self):
        if self.amount == self.total_amount:
            self.cek_p = True
        else :
            self.cek_p = False

    @api.depends('seq')
    def com_name(self):
        if self.seq != False:
            self.name = self.seq
            cekp = self.env['inheriet.journal.payment.sheet'].search([('id_jps', '=', self.id_jpss)])
            self.line_jp = cekp
            self.cek_rem()

    @api.onchange('id_ref_sheet')
    def onchange_id_ref_sheet(self):
        if self.id_ref_sheet != False:
            self.remark = self.id_ref_sheet.name
            self.amount = self.id_ref_sheet.debit
            self.id_jpss = self.id_ref_sheet.id


    def _compute_total_sum(self):
        if self.id_ref_sheet != False:
            self.total_amount = sum(self.line_jp.mapped('amount'))
            if self.total_amount < self.amount:
                find = self.env['inheriet.journal.payment.child'].search([('id', '=', self.id_jpss)])
                sql = self.env.cr.execute('UPDATE inheriet_journal_payment_child SET credit=%s,total_sum=%s,state=%s,in_pay=%s,payed=%s WHERE id =%s',
                    (self.total_amount,self.total_amount,'in_p','t','f',find.id,))
            elif self.total_amount == self.amount:
                find = self.env['inheriet.journal.payment.child'].search([('id', '=', self.id_jpss)])
                sql = self.env.cr.execute('UPDATE inheriet_journal_payment_child SET credit=%s,total_sum=%s,state=%s,in_pay=%s,payed=%s WHERE id =%s',
                    (self.total_amount,self.total_amount,'pay','f','t',find.id,))
            elif self.total_amount == 0:
                self.cost_cnt == False
            if self.total_amount > self.amount:
                raise UserError(_('Fill in the correct amount'))

    @api.onchange('cost_cnt')
    def onchange_cost_cnt(self):
        if self.cost_cnt.id != False:
            self.env['cost.center']
            sql = """SELECT id,name,perc_c,period 
            FROM "cost_center_child" 
            WHERE cost_id=%s"""
            cr= self.env.cr
            cr.execute(sql,(self.cost_cnt.id,))
            result= cr.fetchall()
            for res in result:
                idcc = res[0]
                namecc = res[1]
                pctcc = res[2]
                percc = res[3]
                self.env['inheriet.journal.payment.sheet'].create({
                    'id'    : '',
                    'jp_id' : self.id,
                    'name'  : self.remark,
                    'id_jps': self.id_jpss,
                    'cost_cen'  : idcc,
                    'pct'   : pctcc,
                    'amount': (pctcc * self.amount_p)/100
                    })
                self._compute_total_sum()

class InherietJournalPaymentSheet(models.Model):
    _name = 'inheriet.journal.payment.sheet'

    name = fields.Char()
    coa = fields.Many2one('account.account', string="Account")
    amount = fields.Float(string="Amount")
    jp_id = fields.Many2one('inheriet.journal.payment')
    jps_id = fields.Many2one('inheriet.journal.payment.child')
    mj_id = fields.Many2one('memorial.journal')
    expenses_id = fields.Many2one('hr.expense.sheet')
    pct = fields.Float(string="Pct")
    cost_cen = fields.Many2one('cost.center.child')
    id_jps = fields.Char()

    @api.onchange('cost_cen')
    def change_cost_cen (self):
        for rec in self:
            rec.pct = rec.cost_cen.perc_c
            rec.amount = rec.jp_id.amount_p*rec.pct/100

    @api.onchange('name')
    def change_name (self):
        self.name = self.jp_id.remark
        self.id_jps = self.jp_id.id_jpss

    @api.onchange('amount')
    def change_amount (self):
        if self.id_jps != False:
            finds = self.env['inheriet.journal.payment.sheet'].search([('id_jps', '=', self.id_jps)])
            finds_p = self.env['inheriet.journal.payment'].search([('id_jpss', '=', self.id_jps)])
            am_py = finds_p['amount']
            finds_a = self.env['inheriet.journal.payment.sheet'].search([('id', '=', self.ids)])
            answ = finds_a['amount']
            prog = (sum(finds.mapped('amount')) - answ) + self.amount
            if prog > am_py:
                raise UserError(_('Fill in the correct amount'))




class InherietJournalPaymentChild(models.Model):
    _name = 'inheriet.journal.payment.child'

    name = fields.Char()
    coa = fields.Many2one('account.account', string="Account")
    debit = fields.Float(string="Debit")
    credit = fields.Float(string="Credit")
    line_jps = fields.One2many('inheriet.journal.payment.sheet','jps_id')
    mj_id = fields.Many2one('memorial.journal')
    expenses_id = fields.Many2one('hr.expense.sheet')
    state = fields.Selection(selection=[
            ('in_p', 'In Payment'),
            ('pay', 'Paid')],string="Status",compute='bayar')
    in_pay = fields.Boolean('In Payment')
    payed = fields.Boolean('Paid')
    my_id = fields.Char('My Id',compute='change_namez')
    total_sum = fields.Float(compute='_compute_total_sum',string="Total Amount")

    @api.depends('name')
    def change_namez (self):
        if self.name != False:
            self.my_id = self.id
            cek_pay = self.env['inheriet.journal.payment.sheet'].search([('id_jps', '=', self.my_id)])
            self.line_jps = cek_pay
        else:
            self.my_id = 0

    def bayar(self):
        for rec in self:
            if rec.credit < rec.debit:
                rec.state = 'in_p'
                rec.in_pay = True
                rec.payed = False
            elif rec.credit == rec.debit:
                rec.state = 'pay'
                rec.in_pay = False
                rec.payed = True

    def _compute_total_sum(self):
        if self.name != False:
            self.total_sum = sum(self.line_jps.mapped('amount'))
            self.credit = self.total_sum

class MemorialJournal(models.Model):
    _name = 'memorial.journal'

    @api.model
    def _get_default_seqs(self):
        return self.env["ir.sequence"].next_by_code("memorial.journal.sequence")

    seq = fields.Char(default=_get_default_seqs)
    name = fields.Char()
    ref = fields.Selection(selection=[
            ('Journal Payment', 'Journal Payment')],string="Journal")
    jpc = fields.One2many('inheriet.journal.payment.child','mj_id', string="Journal Payment",
    	domain="[('mj_id','=',False)]")

    @api.onchange('seq')
    def change_seq (self):
    	self.name = self.seq




