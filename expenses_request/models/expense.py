
import re

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero

class Inherit_expenses_sheet(models.Model):
    _inherit = 'hr.expense.sheet'

    payment_mode = fields.Selection([
        ("own_account", "Employee (to reimburse)"),
        ("company_account", "Company")
    ], default='own_account', states={'draft': [('readonly', False)], 'submit': [('readonly', False)], 'approve': [('readonly', False)],'post': [('readonly', True)],'done': [('readonly', True)],'cancel': [('readonly', True)]},store=True, string="Paid By")

    @api.onchange('payment_mode')
    def onchange_payment_mode(self):
        print("tes update mode",self._origin.id)
        print(self.id," id")
        hr_exp = self.env['hr.expense'].sudo().search([('sheet_id','=',self._origin.id)])
        print(hr_exp," hr_exp")
        hr_exp.sudo().update({'payment_mode':self.payment_mode})

    def codes_mode(self):
        hr_exp = self.env['hr.expense'].sudo().search([('sheet_id','=',self._origin.id)])
        hr_exp.sudo().update({'codes':self.codes,'codee':self.codes})

    def update_code(self):
        hr_exp = self.env['hr.expense'].sudo().search([('sheet_id','=',self._origin.id)])
        hr_exp.sudo().update({'codes':self.codes,'codee':self.codes})

class Inherit_expenses(models.Model):
    _inherit = 'hr.expense'

    @api.model    
    def _get_my_department(self):
        employees = self.env.user.employee_ids
        return (
            employees[0].department_id
            if employees
            else self.env["hr.department"] or False
        )

    expense_reg_id          = fields.Many2one('expenses.request', string="Request Id")
    expenses_count          = fields.Integer('Count',compute="compute_count")
    atas_nama               = fields.Char()
    no_rek                  = fields.Char(required=True)
    # bank_name               = fields.Many2one('res.bank')
    bank_name               = fields.Char()
    vendors                 = fields.Many2one('res.partner', string='Vendor',
        change_default=True, tracking=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="You can find a vendor by its Name, TIN, Email or Internal Reference.")
    planned_amount          = fields.Float()
    practicals_amount       = fields.Float()
    sisa_budget             = fields.Float()
    payment_mode = fields.Selection([
        ("company_account", "Company"),
        ("own_account", "Employee (to reimburse)")
    ], default='own_account', string="Paid By")
    account_id = fields.Many2one('account.account', string='Account', default=False, domain="[('internal_type', '=', 'other'), ('company_id', '=', company_id)]", help="An expense account is expected")
    attachment_number = fields.Integer('Number of Attachments', compute='_compute_attachment_number')
    tanpa_budget = fields.Boolean()
    out_budget  = fields.Boolean()    
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account',
        check_company=True, domain="['|',('company_id', '=', company_id),('company_id', '=', False),('group_id', '=', analytic_account_group)]")
    testing = fields.Char()
    total_ongoing = fields.Float(compute='total_ongoings')
    total_amount = fields.Monetary("Total", compute='_compute_amount', store=True, currency_field='currency_id',tracking=True)
    department_id = fields.Many2one("hr.department", "Department", default=_get_my_department,required=True)
    analytic_account_group = fields.Many2one('account.analytic.group',domain="[('name', '=', testnam)]")
    testnam = fields.Char()
    codesname = fields.Char()
    test_department = fields.Many2one(related='department_id.parent_id', readonly=False)
    parent_depart = fields.Char()

    codes = fields.Char(
        string="Request Reference",
        track_visibility="onchange",
    )
    codee = fields.Char()
    ceks_user = fields.Boolean(string="check field", compute='cek_user')
    akses_user = fields.Boolean(string="akses user", compute='akses_users')
    account_date = fields.Date()
    cost_center = fields.Many2one('cost.center.child')
    exp_account_id = fields.Many2one('account.account', string="Exp Account")
    status_saldo_budget = fields.Char()
    end_date = fields.Date()
    date_ku = fields.Char()
    id_budget = fields.Char()
    cros_id = fields.Char()
    cros_tgl = fields.Char()
    hasil_pract = fields.Float()

    @api.onchange('analytic_account_group')
    def onchange_analytic_account_group(self):
        if self.analytic_account_group:
            cari_state = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.state','=','validate'),
                ('grouping_id','=',self.analytic_account_group.id)])
            id_list = []
            for rec in cari_state:
                id_list.append(rec.analytic_account_id.id)
            res = {}
            res ['domain'] = {'analytic_account_id': [('id','in',id_list)]}
            return res

    @api.onchange('analytic_account_id')
    def _onchange_analytic_account_id(self):
        amount = []
        amounts = []
        practs = []
        stat_cros = self.env['crossovered.budget.lines'].search(['|',('crossovered_budget_id.state','=','validate'),('crossovered_budget_id.state','=','validate'),('status', '!=', 'close'),('analytic_account_id', '=', self.analytic_account_id.id)])
        print("yyyyyyyyyyyyyyy",stat_cros.status)
        if stat_cros.id != False:
            for x in stat_cros:
                amount.append(x.planned_amount)
                amounts.append(x.remaining_amount)
                practs.append(x.practical_amount)
                self.account_date = x.date_from
                self.end_date = x.date_to
                self.id_budget = x.id
                self.cros_id = x.crossovered_budget_id.id
                self.cros_tgl = x.date_to
                remain_am = sum(amounts)
                self.planned_amount = sum(amount)*-1
                self.practicals_amount = sum(practs)
                self.sisa_budget = (self.planned_amount + self.practicals_amount)-(0+self.total_ongoing)
        elif stat_cros.id == False:
            self.planned_amount = 0
            self.practicals_amount = 0
            self.sisa_budget = 0
            self.account_date = ''
            self.end_date = ''
            self.id_budget = False
            self.cros_id = 0
            self.cros_tgl = ''


        # amounts = []
        # stat_cross = self.env['crossovered.budget.lines'].search([('status', '!=', 'close'),('analytic_account_id', '=', self.analytic_account_id.id),
        #     ('date_from', '>=', self.account_date),('date_from', '<=', self.account_date)])
        # if self.analytic_account_id:
        #     for x in self.analytic_account_id.crossovered_budget_line and stat_cross:
        #         amounts.append(x.practical_amount)
        #     self.practicals_amount = sum(amounts)
        #     self.total_ongoings()
        #     self.sisa_budget = (self.planned_amount * -1)+self.practicals_amount-self.total_ongoing
        #     self.planned_amounts = self.planned_amount
        #     self.cari_pract()
        #     self.practicals_amounts = self.practicals_amount + self.hasil_pract
        #     self.sisa_budgets = self.sisa_budget + self.hasil_pract
        #     self.sisa_budget = self.sisa_budgets

    # @api.onchange('account_date')
    # def onchange_next(self):
    #     if self.account_date != False:
    #         self.date_ku =self.account_date
    #         print('--------------------------', self.date_ku)
    #         date_1= datetime.strptime(self.date_ku, "%Y-%m-%d")
    #         self.end_date = date_1.replace(day=28)
    #         sql = """SELECT id,status,crossovered_budget_id
    #         FROM crossovered_budget_lines
    #         WHERE date_from >=%s AND date_to <=%s
    #         OR date_to >=%s AND date_from <=%s
    #         AND analytic_account_id=%s"""
    #         cr= self.env.cr
    #         cr.execute(sql,(self.account_date,self.end_date,
    #             self.account_date,self.end_date,self.analytic_account_id.id,))
    #         results= cr.fetchall()
    #         for res in results:
    #             budget = res[0]
    #             status = res[1]
    #             cro_id = res[2]
    #             print('===================', budget)
    #             self.id_budget = budget
    #             self.status_saldo_budget = status
    #             self.cros_id = cro_id
    #     remain_amount = []
    #     amounts = []
    #     amount = []
    #     stat_cros = self.env['crossovered.budget.lines'].search(['|',('date_from', '>=', self.account_date),
    #         ('date_to', '<=', self.end_date),('date_to', '>=', self.account_date),
    #         ('date_from', '<=', self.end_date),('analytic_account_id', '=', self.analytic_account_id.id)])
    #     if self.analytic_account_id:
    #         for x in self.analytic_account_id.crossovered_budget_line and stat_cros:
    #             amounts.append(x.practical_amount)
    #             amount.append(x.planned_amount)
    #             remain_amount.append(x.remainings_amount)
    #         self.planned_amount = sum(amount)
    #         self.practicals_amount = sum(amounts)
    #         hasil_remain_amount = sum(remain_amount)
    #         self.total_ongoings()
    #         # print("Plan amount", self.planned_amount)
    #         # print("Practical amount", self.practicals_amount)
    #         # print("Total ongoing", self.total_ongoing)
    #         # print("Remaining amount", hasil_remain_amount)
    #         # print("Remaining amount", hasil_remain_amount)
    #         # self.sisa_budget = (self.planned_amount * -1)+self.practicals_amount-self.total_ongoing
    #         # self.sisa_budget = (hasil_remain_amount * -1)-self.total_ongoing
    #         self.sisa_budget = (hasil_remain_amount * -1)
    #         self.planned_amounts = self.planned_amount
    #         # self.cari_pract()
    #         # self.practicals_amounts = self.practicals_amount + self.hasil_pract
    #         # self.sisa_budgets = self.sisa_budget + self.hasil_pract
    #         # self.sisa_budget = self.sisa_budgets
    #         self.practicals_amounts = self.practicals_amount
    #         self.sisa_budgets = self.sisa_budget
    #         self.sisa_budget = self.sisa_budgets

    def action_move_create(self):
        '''
        main function that is called when trying to create the accounting entries related to an expense
        '''
        move_group_by_sheet = self._get_account_move_by_sheet()

        move_line_values_by_expense = self._get_account_move_line_values()

        move_to_keep_draft = self.env['account.move']

        company_payments = self.env['account.payment']

        for expense in self:
            company_currency = expense.company_id.currency_id
            different_currency = expense.currency_id != company_currency

            # get the account move of the related sheet
            move = move_group_by_sheet[expense.sheet_id.id]

            # get move line values
            move_line_values = move_line_values_by_expense.get(expense.id)
            move_line_dst = move_line_values[-1]
            total_amount = move_line_dst['debit'] or -move_line_dst['credit']
            total_amount_currency = move_line_dst['amount_currency']

            # create one more move line, a counterline for the total on payable account
            if expense.payment_mode == 'company_account':
                if not expense.sheet_id.bank_journal_id.default_credit_account_id:
                    raise UserError(_("No credit account found for the %s journal, please configure one.") % (expense.sheet_id.bank_journal_id.name))
                journal = expense.sheet_id.bank_journal_id
                # create payment
                payment_methods = journal.outbound_payment_method_ids if total_amount < 0 else journal.inbound_payment_method_ids
                journal_currency = journal.currency_id or journal.company_id.currency_id
                payment = self.env['account.payment'].create({
                    'payment_method_id': payment_methods and payment_methods[0].id or False,
                    'payment_type': 'outbound' if total_amount < 0 else 'inbound',
                    'partner_id': expense.employee_id.address_home_id.commercial_partner_id.id,
                    'partner_type': 'supplier',
                    'journal_id': journal.id,
                    'payment_date': expense.date,
                    'state': 'draft',
                    'currency_id': expense.currency_id.id if different_currency else journal_currency.id,
                    'amount': abs(total_amount_currency) if different_currency else abs(total_amount),
                    'name': expense.name,
                    'status_saldo_budget': expense.status_saldo_budget,
                })
                move_line_dst['payment_id'] = payment.id

            # link move lines to move, and move to expense sheet
            move.write({'line_ids': [(0, 0, line) for line in move_line_values]})
            expense.sheet_id.write({'account_move_id': move.id})

            if expense.payment_mode == 'company_account':
                company_payments |= payment
                if journal.post_at == 'bank_rec':
                    move_to_keep_draft |= move

                expense.sheet_id.paid_expense_sheets()

        company_payments.filtered(lambda x: x.journal_id.post_at == 'pay_val').write({'state':'reconciled'})
        company_payments.filtered(lambda x: x.journal_id.post_at == 'bank_rec').write({'state':'posted'})

        # post the moves
        for move in move_group_by_sheet.values():
            if move in move_to_keep_draft:
                continue
            move.post()

        return move_group_by_sheet

    def _prepare_move_values(self):
        """
        This function prepares move values related to an expense
        """
        self.ensure_one()
        journal = self.sheet_id.bank_journal_id if self.payment_mode == 'company_account' else self.sheet_id.journal_id
        account_date = self.sheet_id.accounting_date or self.date
        move_values = {
            'journal_id': journal.id,
            'company_id': self.sheet_id.company_id.id,
            'date': account_date,
            'ref': self.sheet_id.name,
            'status_saldo_budget': self.status_saldo_budget,
            # force the name to the default value, to avoid an eventual 'default_name' in the context
            # to set it to '' which cause no number to be given to the account.move when posted.
            'name': '/',
        }
        return move_values

    def _get_account_move_line_values(self):
        move_line_values_by_expense = {}
        for expense in self:
            move_line_name = expense.employee_id.name + ': ' + expense.name.split('\n')[0][:64]
            account_src = expense._get_expense_account_source()
            account_dst = expense._get_expense_account_destination()
            account_date = expense.sheet_id.accounting_date or expense.date or fields.Date.context_today(expense)

            company_currency = expense.company_id.currency_id
            different_currency = expense.currency_id and expense.currency_id != company_currency

            move_line_values = []
            taxes = expense.tax_ids.with_context(round=True).compute_all(expense.unit_amount, expense.currency_id, expense.quantity, expense.product_id)
            total_amount = 0.0
            total_amount_currency = 0.0
            partner_id = expense.employee_id.address_home_id.commercial_partner_id.id

            # source move line
            amount = taxes['total_excluded']
            amount_currency = False
            if different_currency:
                amount = expense.currency_id._convert(amount, company_currency, expense.company_id, account_date)
                amount_currency = taxes['total_excluded']
            move_line_src = {
                'name': move_line_name,
                'quantity': expense.quantity or 1,
                'debit': amount if amount > 0 else 0,
                'credit': -amount if amount < 0 else 0,
                'amount_currency': amount_currency if different_currency else 0.0,
                'account_id': account_src.id,
                'product_id': expense.product_id.id,
                'product_uom_id': expense.product_uom_id.id,
                'analytic_account_id': expense.analytic_account_id.id,
                'analytic_tag_ids': [(6, 0, expense.analytic_tag_ids.ids)],
                'expense_id': expense.id,
                'status_saldo_budget': expense.status_saldo_budget,
                'partner_id': partner_id,
                'tax_ids': [(6, 0, expense.tax_ids.ids)],
                'tag_ids': [(6, 0, taxes['base_tags'])],
                'currency_id': expense.currency_id.id if different_currency else False,
            }
            move_line_values.append(move_line_src)
            total_amount += -move_line_src['debit'] or move_line_src['credit']
            total_amount_currency += -move_line_src['amount_currency'] if move_line_src['currency_id'] else (-move_line_src['debit'] or move_line_src['credit'])

            # taxes move lines
            for tax in taxes['taxes']:
                amount = tax['amount']
                amount_currency = False
                if different_currency:
                    amount = expense.currency_id._convert(amount, company_currency, expense.company_id, account_date)
                    amount_currency = tax['amount']
                move_line_tax_values = {
                    'name': tax['name'],
                    'quantity': 1,
                    'debit': amount if amount > 0 else 0,
                    'credit': -amount if amount < 0 else 0,
                    'amount_currency': amount_currency if different_currency else 0.0,
                    'account_id': tax['account_id'] or move_line_src['account_id'],
                    'tax_repartition_line_id': tax['tax_repartition_line_id'],
                    'tag_ids': tax['tag_ids'],
                    'tax_base_amount': tax['base'],
                    'expense_id': expense.id,
                    'status_saldo_budget': expense.status_saldo_budget,
                    'partner_id': partner_id,
                    'currency_id': expense.currency_id.id if different_currency else False,
                    'analytic_account_id': expense.analytic_account_id.id if tax['analytic'] else False,
                    'analytic_tag_ids': [(6, 0, expense.analytic_tag_ids.ids)] if tax['analytic'] else False,
                }
                total_amount -= amount
                total_amount_currency -= move_line_tax_values['amount_currency'] or amount
                move_line_values.append(move_line_tax_values)

            # destination move line
            move_line_dst = {
                'name': move_line_name,
                'debit': total_amount > 0 and total_amount,
                'credit': total_amount < 0 and -total_amount,
                'account_id': account_dst,
                'date_maturity': account_date,
                'amount_currency': total_amount_currency if different_currency else 0.0,
                'currency_id': expense.currency_id.id if different_currency else False,
                'expense_id': expense.id,
                'partner_id': partner_id,
                'status_saldo_budget': expense.status_saldo_budget,
            }
            move_line_values.append(move_line_dst)

            move_line_values_by_expense[expense.id] = move_line_values
        return move_line_values_by_expense

    def copy(self):
        for expense in self:
            if expense.ceks_user == True:
                raise UserError(_('You are not allowed to duplicate!'))
        return super(Inherit_expenses, self).copy()

    def unlink(self):
        for expense in self:
            if expense.ceks_user == True:
                raise UserError(_('You are not allowed to delete!'))
        return super(Inherit_expenses, self).unlink()

    def cek_user(self):
        for cek in self:
            if cek.user_has_groups("expenses_request.expenses_request_user") and not cek.user_has_groups("expenses_request.expenses_request_vip_akses") and not cek.user_has_groups("base.group_erp_manager"):
                self.ceks_user = True
            else:
                self.ceks_user = False

    def akses_users(self):
        for akses in self:
            if self.ceks_user == True and self.state != 'draft':
                self.akses_user = True
            else:
                self.akses_user = False

    @api.depends('id_budget')
    def total_ongoings(self):
        if self.tanpa_budget == False :
            query = """ 
                        SELECT sum(dt.jml) as total
                        FROM (
                            SELECT sum(ex.total_amount) AS jml
                            FROM hr_expense ex
                            LEFT JOIN hr_expense_sheet exps on ex.sheet_id = exps.id
                            WHERE (exps.state ='draft' OR exps.state='submit' OR exps.state='approve' OR exps.state is Null)
                            AND ex.analytic_account_id=%s AND ex.id_budget = %s
                            UNION ALL
                            SELECT sum(estimated_cost) AS jml
                            FROM purchase_request_line
                            WHERE request_state != 'rejected' AND request_state != 'done'
                            AND analytic_account_id="""+str(int(self.analytic_account_id.id))+"""
                        ) dt
                        """
            self.env.cr.execute(query,(str(int(self.analytic_account_id.id)),str(int(self.id_budget)),))
            print("query",query)
            # self.env.cr.execute(""" SELECT sum(s.total_amount) AS total FROM hr_expense s WHERE analytic_account_id=%s AND (state != 'done' AND state != 'refused') """,(self.analytic_account_id.id,))
            total_expense  = self.env.cr.dictfetchall()
            for data in total_expense :
                self.total_ongoing = data['total']
                # print("Total outstanding",self.total_ongoing)
        else :
            self.total_ongoing = 0
            # print("Total outstanding 2",self.total_ongoing)
        # data_obj    = self.env['hr.expense']
        # for data in self:
        #     list_data        = data_obj.search([('total_amount')])
        #     data.example_count = sum(list_data)

    @api.onchange('department_id')
    def _onchange_department_ids(self):
            if self.department_id:
                self.cek_user()
                self.write({'testnam' : self.department_id.name})                

    @api.onchange('test_department')
    def _onchange_test_department_ids(self):
            if self.test_department:
                self.write({'testnam' : self.test_department.name})

    @api.onchange('total_amount')
    def _onchange_aksi(self):
        total_sisa = self.sisa_budget
        total_dari_amount = self.total_amount
        if (total_dari_amount > total_sisa) and (self.tanpa_budget == False):
            self.analytic_account_id = ""
            self.planned_amount = 0
            self.practicals_amount = 0
            self.sisa_budget = 0
            self.unit_amount = 0
            self.total_amount = 0
            raise UserError(_("Budget not enough! Choose other Budget"))

    @api.onchange('tanpa_budget')
    def _onchange_aksiku(self):
        for rec in self:
            if rec.tanpa_budget == True and self._origin.id != False:
                self.analytic_account_id = ""
                self.analytic_account_group = ""
                self.planned_amount = 0
                self.practicals_amount = 0
                self.sisa_budget = 0
                self.unit_amount = 0
                self.total_amount = 0
                self.env.cr.execute('UPDATE hr_expense SET analytic_account_group=NULL WHERE id={0}'.format(self._origin.id))
                self.env.cr.execute('UPDATE hr_expense SET analytic_account_id=NULL WHERE id={0}'.format(self._origin.id))
            elif rec.tanpa_budget == True and self._origin.id == False:
                self.analytic_account_id = ""
                self.analytic_account_group = ""
                self.planned_amount = 0
                self.practicals_amount = 0
                self.sisa_budget = 0
                self.unit_amount = 0
                self.total_amount = 0

    @api.onchange('product_id', 'company_id')
    def _onchange_product_id(self):
        if self.product_id:
            if not self.name:
                self.name = self.product_id.display_name or ''
            if not self.attachment_number or (self.attachment_number and not self.unit_amount):
                self.unit_amount = self.product_id.price_compute('standard_price')[self.product_id.id]
            self.product_uom_id = self.product_id.uom_id
            self.tax_ids = self.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == self.company_id)  # taxes only from the same company
            account = self.product_id.product_tmpl_id._get_product_accounts()['expense']

    @api.depends('employee_id')
    def _compute_is_editable(self):
        self.codee = self.codes
        is_account_manager = self.env.user.has_group('account.group_account_invoice') or self.env.user.has_group('account.group_account_user') or self.env.user.has_group('account.group_account_manager')
        for expense in self:
            if expense.state == 'draft' or expense.sheet_id.state in ['draft', 'submit']:
                expense.is_editable = True
            elif expense.sheet_id.state == 'approve':
                expense.is_editable = is_account_manager
            else:
                expense.is_editable = False

    def _create_sheet_from_expenses(self):
        if any(expense.state != 'draft' or expense.sheet_id for expense in self):
            raise UserError(_("You cannot report twice the same line!"))
        if len(self.mapped('employee_id')) != 1:
            raise UserError(_("You cannot report expenses for different employees in the same report."))
        if any(not expense.product_id for expense in self):
            raise UserError(_("You can not create report without product."))

        todo = self.filtered(lambda x: x.payment_mode=='own_account') or self.filtered(lambda x: x.payment_mode=='company_account')
        sheet = self.env['hr.expense.sheet'].create({
            'company_id': self.company_id.id,
            'employee_id': self[0].employee_id.id,
            'name': todo[0].name if len(todo) == 1 else '',
            'testnam': todo[0].testnam if len(todo) == 1 else '',
            'expense_line_ids': [(6, 0, todo.ids)]
        })
        sheet._onchange_employee_id()
        return sheet

    def action_submit_expenses(self):
        if (self.unit_amount == 0):
            raise UserError(_("Fill in the correct unit price"))
        sheet = self._create_sheet_from_expenses()
        return {
            'name': _('New Expense Report'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.expense.sheet',
            'target': 'current',
            'res_id': sheet.id,
        }


class Inherit_expenses_sheet(models.Model):
    _inherit = 'hr.expense.sheet'

    approve_mg                  = fields.Boolean('Approve Manager')
    approve_gm                  = fields.Boolean('Approve General Manager')
    approve_direktur            = fields.Boolean('Approve Direktur')
    approve_manager_direktur    = fields.Boolean('Approve Managing Direktur')
    approve_mg_budget                  = fields.Boolean('Approve Manager')
    approve_corporate                  = fields.Boolean('Approve Corporate')
    approve_bendahara_ypk            = fields.Boolean('Approve Bendahara')
    deskripsi_approve           = fields.Char(string="Approval Status", readonly=True)
    deskripsi_approve_budget           = fields.Char(string="Approval Budget Status", readonly=True)
    atas_nama               = fields.Char(related='expense_line_ids.atas_nama')
    no_rek                  = fields.Char(related='expense_line_ids.no_rek')
    # bank_name               = fields.Many2one(related='expense_line_ids.bank_name')
    bank_name               = fields.Char()
    vendors                 = fields.Many2one(related='expense_line_ids.vendors')
    codes                 = fields.Char()
    total_amount = fields.Monetary('Total Amount', currency_field='currency_id', compute='_compute_amount', store=True)
    ceks_user = fields.Boolean(string="check field", compute='cek_user')
    testnam = fields.Char()
    receipt_list = fields.Many2many('res.users')
    email_cc = fields.Many2many('res.users','login')
    userku_id = fields.Many2one('res.users')
    jurnal_number = fields.Integer('Number of Jurnal')
    jurnal_count = fields.Integer(compute='compute_jurnal_count')
    notes = fields.Text()

    def apbudget(self):
        if self.deskripsi_approve_budget == 'Done':
            self.deskripsi_approve_budgets = 'Done'
            self.action_get_jurnal_payment_view()
        else:
            self.deskripsi_approve_budgets = ''

    def cancels(self):
        for rec in self:
            rec.action_cancel()

    def postes(self):
        for rec in self:
            rec.action_sheet_move_create()

    def copy(self):
        for expense in self:
            if expense.ceks_user == True:
                raise UserError(_('You are not allowed to duplicate!'))
        return super(Inherit_expenses_sheet, self).copy()

    def unlink(self):
        for expense in self:
            if expense.ceks_user == True:
                raise UserError(_('You are not allowed to delete!'))
        return super(Inherit_expenses_sheet, self).unlink()

    def cek_user(self):
        for cek in self:
            if cek.user_has_groups("expenses_request.expenses_request_user") and not cek.user_has_groups("base.group_erp_manager"):
                self.ceks_user = True
            else:
                self.ceks_user = False

    def reset_expense_sheets(self):
        self.status = ''
        self.status_budget = ''
        if not self.can_reset:
            raise UserError(_("Only HR Officers or the concerned employee can reset to draft."))
        self.mapped('expense_line_ids').write({'is_refused': False})
        self.write({'state': 'draft'})
        self.activity_update()
        return True

    status = fields.Selection(selection=[
            ('wait_manager', 'Wait For Manager Approve'),
            ('wait_general_manager', 'Wait For Dekan'),
            ('wait_direktur', 'Wait For Warek'),
            ('wait_manager_direktur', 'Wait For Rektor'),
            ('approve', 'Approved')],
            string='Status',track_visibility="onchange")

    status_budget = fields.Selection(selection=[
            ('wait_manager_budget', 'Wait For Budget Manager Approve'),
            ('wait_corporate', 'Wait For Budget Corporate'),
            ('wait_bendahara_ypk', 'Wait For Bendahara YPK')],
            string='Status',track_visibility="onchange")

    @api.depends('expense_line_ids.total_amount_company')
    def _compute_amount(self):
        for sheet in self:
            sheet.total_amount = sum(sheet.expense_line_ids.mapped('total_amount_company'))
        if(self.state == "submit"):
            self.status = ''
            self.status_budget = ''
            self.request_approval()
    
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.address_id = self.employee_id.sudo().address_home_id
        self.department_id = self.employee_id.department_id
        self.user_id = self.employee_id.expense_manager_id or self.employee_id.parent_id.user_id

    def compute_jurnal_count(self):
        for rec in self:
            rec.jurnal_count = self.env['inheriet.journal.payment.child'].search_count(
            [('expenses_id', '=', self.id)]
            )

    def action_get_jurnal_payment_view(self):
        if self.jurnal_count == 0:
            sql = """SELECT name,total_amount,exp_account_id
            FROM hr_expense
            WHERE sheet_id=%s
            ORDER BY id DESC"""
            cr= self.env.cr
            cr.execute(sql,(self.id,))
            results= cr.fetchall()
            for res in results:
                nm = res[0]
                ta = res[1]
                exp_coa = res[2]
                new_jp = self.env['inheriet.journal.payment.child'].create({
                    'name'  : nm,
                    'debit'  : ta,
                    'coa'  : exp_coa,
                    'expenses_id' : self.id
                    })
            self.ensure_one()
            return{
            'type':'ir.actions.act_window',
            'name' : self.name,
            'view_mode': 'tree,form',
            'res_model': 'inheriet.journal.payment.child',
            'domain': [('expenses_id', '=', self.id)],
            'context': "{'create': True}"
            }
        elif self.jurnal_count >= 0:
            self.ensure_one()
            return{
            'type':'ir.actions.act_window',
            'name' : self.name,
            'view_mode': 'tree,form',
            'res_model': 'inheriet.journal.payment.child',
            'domain': [('expenses_id', '=', self.id)],
            'context': "{'create': False}"
            }

    def request_approval(self):
        a = "FAKULTAS BISNIS DAN KOMUNIKASI"
        b = "FAKULTAS ILMU KOMPUTER DAN DESAIN"
        c = "ENTREPRENEUR AND BUSINESS"
        d = "MARKETING"
        e = "PROJECT"
        f = "REKTORAT"
        g = "QUALITY ASSURANCE"
        h = "FINANCE - INCOME CONTROLLER"
        i = "MARKETING - RECRUITMENT"
        j = "MARKETING - BRAND COMMUNICATIONS"
        nominal = self.total_amount
        testnam = self.testnam
        if nominal == 0:
            raise UserError(_("Fill in the correct unit price"))
        if ((testnam != a and testnam != b and testnam != c and testnam != d and testnam != e) and nominal < 1000000):
            self.approve_mg = True
            self.approve_gm = False
            self.approve_direktur = False
            self.approve_manager_direktur = False
            self.approve_mmanager_direktur = False
            self.approve_mg_budget = True
            self.approve_corporate = False
            self.approve_bendahara_ypk = False
            self.write({'state': 'submit'})
            self.deskripsi_approve = "Kaprodi/Manager"
            self.deskripsi_approve_budget = "Budget Manager"
        elif ((testnam == a or testnam == b or testnam == c) and nominal < 1000000):
            self.approve_mg = True
            self.approve_gm = True
            self.approve_direktur = False
            self.approve_manager_direktur = False
            self.approve_mmanager_direktur = False
            self.approve_mg_budget = True
            self.approve_corporate = False
            self.approve_bendahara_ypk = False
            self.write({'state': 'submit'})
            self.deskripsi_approve = "Kaprodi/Manager > Dekan"
            self.deskripsi_approve_budget = "Budget Manager"
        elif ((testnam == i or testnam == j) and nominal < 1000000):
            self.approve_mg = True
            self.approve_gm = True
            self.approve_direktur = True
            self.approve_manager_direktur = False
            self.approve_mmanager_direktur = False
            self.approve_mg_budget = True
            self.approve_corporate = False
            self.approve_bendahara_ypk = False
            self.write({'state': 'submit'})
            self.deskripsi_approve = "Kaprodi/Manager > Dekan"
            self.deskripsi_approve_budget = "Budget Manager"
        elif ((testnam == h) and nominal < 1000000):
            self.approve_mg = True
            self.approve_gm = False
            self.approve_direktur = False
            self.approve_manager_direktur = False
            self.approve_mmanager_direktur = False
            self.approve_mg_budget = True
            self.approve_corporate = False
            self.approve_bendahara_ypk = False
            self.write({'state': 'submit'})
            self.deskripsi_approve = "Kaprodi/Manager"
            self.deskripsi_approve_budget = "Budget Manager"
        elif ((testnam == d or testnam == e) and nominal < 1000000):
            self.approve_mg = True
            self.approve_gm = True
            self.approve_direktur = True
            self.approve_manager_direktur = False
            self.approve_mmanager_direktur = False
            self.approve_mg_budget = True
            self.approve_corporate = False
            self.approve_bendahara_ypk = False
            self.write({'state': 'submit'})
            self.deskripsi_approve = "Kaprodi/Manager > Dekan > Warek"
            self.deskripsi_approve_budget = "Budget Manager"
        elif ((testnam == h or testnam == i or testnam == j) and (nominal >= 1000000 and nominal < 10000000)):
            self.approve_mg = True
            self.approve_gm = True
            self.approve_direktur = True
            self.approve_manager_direktur = False
            self.approve_mmanager_direktur = False
            self.approve_mg_budget = True
            self.approve_corporate = False
            self.approve_bendahara_ypk = False
            self.write({"state": "submit"})
            self.deskripsi_approve = "Kaprodi/Manager > Dekan > Warek"
            self.deskripsi_approve_budget = "Budget Manager"
        elif ((testnam != f and testnam != g) and (nominal >= 1000000 and nominal < 10000000)):
            self.approve_mg = True
            self.approve_gm = True
            self.approve_direktur = True
            self.approve_manager_direktur = False
            self.approve_mmanager_direktur = False
            self.approve_mg_budget = True
            self.approve_corporate = False
            self.approve_bendahara_ypk = False
            self.write({"state": "submit"})
            self.deskripsi_approve = "Kaprodi/Manager > Dekan > Warek"
            self.deskripsi_approve_budget = "Budget Manager"
        elif((testnam == f or testnam == g) and (nominal >= 1000000 and nominal < 10000000)):
            self.approve_mg = True
            self.approve_gm = True
            self.approve_direktur = True
            self.approve_manager_direktur = True
            self.approve_mmanager_direktur = False
            self.approve_mg_budget = True
            self.approve_corporate = False
            self.approve_bendahara_ypk = False
            self.write({"state": "submit"})
            self.deskripsi_approve = "Kaprodi/Manager > Dekan > Warek > Rektor"
            self.deskripsi_approve_budget = "Budget Manager"
        elif ((nominal >= 10000000) and (nominal < 50000000)):
            self.approve_mg = True
            self.approve_gm = True
            self.approve_direktur = True
            self.approve_manager_direktur = True
            self.approve_mmanager_direktur = False
            self.approve_mg_budget = True
            self.approve_corporate = True
            self.approve_bendahara_ypk = False
            self.write({"state": "submit"})
            self.deskripsi_approve = "Kaprodi/Manager > Dekan > Warek > Rektor"
            self.deskripsi_approve_budget = "Budget Manager > Corporate"
        elif (nominal >= 50000000):
            self.approve_mg = True
            self.approve_gm = True
            self.approve_direktur = True
            self.approve_manager_direktur = True
            self.approve_mmanager_direktur = False
            self.approve_mg_budget = True
            self.approve_corporate = True
            self.approve_bendahara_ypk = True
            self.write({"state": "submit"})
            self.deskripsi_approve = "Kaprodi/Manager > Dekan > Warek > Rektor"
            self.deskripsi_approve_budget = "Budget Manager > Corporate > Bendahara YPK"
        elif (nominal < 0):
            self.approve_mg = True
            self.approve_gm = False
            self.approve_direktur = False
            self.approve_manager_direktur = False
            self.approve_mmanager_direktur = False
            self.approve_mg_budget = True
            self.approve_corporate = False
            self.approve_bendahara_ypk = False
            self.write({'state': 'submit'})
            self.deskripsi_approve = "Kaprodi/Manager"
            self.deskripsi_approve_budget = "Budget Manager"

    def act_approve_mg(self):
        nominal = self.total_amount
        if ((nominal > 0 and nominal < 1000000) and self.deskripsi_approve == "Kaprodi/Manager"):
            self.deskripsi_approve = "Done"
            self.status ='approve'
            self.approve_mg = False
            self.approve_gm = False
            self.approve_direktur = False
            self.approve_manager_direktur = False
            self.approve_mmanager_direktur = False
        elif((nominal < 0)and self.deskripsi_approve == "Kaprodi/Manager"):
            self.deskripsi_approve = "Done"
            self.status ='approve'
            self.approve_mg = False
        elif(self.deskripsi_approve,'=',"Kaprodi/Manager > Dekan"):
            self.approve_mg = False
            self.status = 'wait_general_manager'
        else:
            self.status = 'submit'

    def act_approve_gm(self):
        nominal = self.total_amount
        if ((nominal > 0 and nominal < 1000000) and self.deskripsi_approve == "Kaprodi/Manager > Dekan"):
            self.deskripsi_approve = "Done"
            self.status ='approve'
            self.approve_gm = False
            self.approve_direktur = False
            self.approve_manager_direktur = False
            self.approve_mmanager_direktur = False
        elif(self.deskripsi_approve,'=',"Kaprodi/Manager > Dekan > Warek"):
            self.approve_gm = False
            self.status = 'wait_direktur'
        else:
            self.state = 'submit'

    def act_approve_dir(self):
        nominal = self.total_amount
        if ((nominal > 0 and nominal < 1000000) and self.deskripsi_approve == "Kaprodi/Manager > Dekan > Warek"):
            self.deskripsi_approve = "Done"
            self.status ='approve'
            self.approve_direktur = False
            self.approve_manager_direktur = False
            self.approve_mmanager_direktur = False
        elif ((nominal >= 1000000 and nominal < 10000000) and self.deskripsi_approve == "Kaprodi/Manager > Dekan > Warek"):
            self.deskripsi_approve = "Done"
            self.status ='approve'
            self.approve_direktur = False
            self.approve_manager_direktur = False
            self.approve_mmanager_direktur = False
        elif(self.deskripsi_approve,'=',"Kaprodi/Manager > Dekan > Warek > Rektor"):
            self.approve_direktur = False
            self.status = 'wait_manager_direktur'
        else:
            self.state = 'submit'

    def act_approve_man_dir(self):
        nominal = self.total_amount
        if ((nominal >= 1000000 and nominal < 10000000) and self.deskripsi_approve == "Kaprodi/Manager > Dekan > Warek > Rektor"):
            self.deskripsi_approve = "Done"
            self.status ='approve'
            self.approve_direktur = False
            self.approve_manager_direktur = False
        if ((nominal >= 10000000 and nominal < 50000000) and self.deskripsi_approve == "Kaprodi/Manager > Dekan > Warek > Rektor"):
            self.deskripsi_approve = "Done"
            self.status ='approve'
            self.approve_direktur = False
            self.approve_manager_direktur = False
        elif ((nominal >= 50000000) and self.deskripsi_approve == "Kaprodi/Manager > Dekan > Warek > Rektor"):
            self.deskripsi_approve = "Done"
            self.status ='approve'
            self.approve_direktur = False
            self.approve_manager_direktur = False
        else:
            self.state = 'submit'

    def act_approve_mg_budget(self):
        self.codes = self.env["ir.sequence"].next_by_code("expense.sequence")
        self.codes_mode()
        nominal = self.total_amount
        if ((nominal > 0) and (nominal < 10000000)):
            self.deskripsi_approve_budget = "Done"
            self.approve_mg_budget = False
            self.approve_corporate = False
            self.approve_bendahara_ypk = False
            self.state = 'approve'
        elif(nominal < 0):
            self.deskripsi_approve_budget = "Done"
            self.approve_mg_budget = False
            self.state = 'approve'           
        elif(self.deskripsi_approve_budget,'=',"Budget Manager > Corporate"):
            self.approve_mg_budget = False
            self.status_budget = 'wait_corporate'
        else:
            self.state = 'submit'

    def act_approve_corporate(self):
        nominal = self.total_amount
        if ((nominal >= 10000000) and (nominal < 50000000)):
            self.deskripsi_approve_budget = "Done"
            self.approve_corporate = False
            self.approve_bendahara_ypk = False
            self.state = 'approve'
        elif(self.deskripsi_approve_budget,'=',"Budget Manager > Corporate > Bendahara YPK"):
            self.approve_corporate = False
            self.status_budget = 'wait_bendahara_ypk'
        else:
            self.state = 'submit'

    def act_approve_bendahara_ypk(self):
        nominal = self.total_amount
        if (nominal >= 50000000):
            self.deskripsi_approve_budget = "Done"
            self.approve_bendahara_ypk = False
            self.state = 'approve'
        else:
            self.state = 'submit'

    def action_cancel(self):
        for sheet in self:
            account_move = sheet.account_move_id
            sheet.account_move_id = False
            payments = self.env["account.payment"].search(
                [("expense_sheet_id", "=", sheet.id), ("state", "!=", "cancelled")]
            )
            # case : cancel invoice from hr_expense
            self._remove_reconcile_hr_invoice(account_move)
            # If the sheet is paid then remove payments
            if sheet.state == "done":
                if sheet.expense_line_ids[:1].payment_mode == "own_account":
                    self._remove_move_reconcile(payments, account_move)
                    self._cancel_payments(payments)
                    self.status = ''
                    self.status_budget = ''
                else:
                    # In this case, during the cancellation the journal entry
                    # will be deleted
                    self._cancel_payments(payments)
                    self.status = ''
                    self.status_budget = ''
                    payments.unlink()
            # Deleting the Journal entry if in the previous steps
            # (if the expense sheet is paid and payment_mode == 'own_account')
            # it has not been deleted
            if account_move.exists():
                if account_move.state != "draft":
                    account_move.button_cancel()
                    self.status = ''
                    self.status_budget = ''
                account_move.with_context({"force_delete": True}).unlink()
            sheet.state = "draft"
        sql = """SELECT id,status_saldo_budget,id_budget,analytic_account_id
        FROM hr_expense
        WHERE sheet_id=%s"""
        cr= self.env.cr
        cr.execute(sql,(self._origin.id,))
        results= cr.fetchall()
        for res in results:
            id_expense = res[0]
            saldo_exp = res[1]
            id_my_budget = res[2]
            analytic_account_my_id = res[3]
            # print('===================', id_expense)
            self.env.cr.execute("""UPDATE account_move_line SET status_saldo_budget=%s WHERE expense_id=%s""",(saldo_exp,id_expense))
            # self.env.cr.execute("""UPDATE crossovered_budget_lines SET planned_amount=planned_amount-%s 
            #     WHERE id>%s AND analytic_account_id=%s""",(self.total_amount,id_my_budget,analytic_account_my_id,))

    def action_sheet_move_create(self):
        res = super().action_sheet_move_create()
        if self.expense_line_ids[0].payment_mode == "company_account":
            self.account_move_id.mapped("line_ids.payment_id").write(
                {"expense_sheet_id": self.id}
            )
        sql = """SELECT id,status_saldo_budget,id_budget,analytic_account_id,cros_tgl
        FROM hr_expense
        WHERE sheet_id=%s"""
        cr= self.env.cr
        cr.execute(sql,(self._origin.id,))
        results= cr.fetchall()
        for res in results:
            id_expense = res[0]
            saldo_exp = res[1]
            id_my_budget = res[2]
            analytic_account_my_id = res[3]
            cros_tgl = res[4]
            print('===================', id_expense)
            self.env.cr.execute("""UPDATE account_move_line SET status_saldo_budget=%s WHERE expense_id=%s""",(saldo_exp,id_expense))
            self.env.cr.execute("""UPDATE crossovered_budget_lines SET planned_amount=planned_amount+%s 
                WHERE id>%s AND analytic_account_id=%s AND date_from<=%s """,(self.total_amount,id_my_budget,analytic_account_my_id,cros_tgl,))
        return res

    def _remove_reconcile_hr_invoice(self, account_move):
        """Cancel invoice made by hr_expense_invoice module automatically"""
        reconcile = account_move.mapped("line_ids.full_reconcile_id")
        aml = self.env["account.move.line"].search(
            [("full_reconcile_id", "in", reconcile.ids)]
        )
        exp_move_line = aml.filtered(lambda l: l.move_id.id != account_move.id)
        # set state to cancel
        exp_move_line.move_id.button_draft()
        exp_move_line.move_id.button_cancel()

    def _remove_move_reconcile(self, payments, account_move):
        """Delete only reconciliations made with the payments generated
        by hr_expense module automatically"""
        reconcile = account_move.mapped("line_ids.full_reconcile_id")

        payments_aml = payments.mapped("move_line_ids")
        aml_unreconcile = payments_aml.filtered(
            lambda r: r.full_reconcile_id in reconcile
        )

        aml_unreconcile.remove_move_reconcile()

    def _cancel_payments(self, payments):
        for rec in payments:
            for move in rec.move_line_ids.mapped("move_id"):
                move.button_cancel()
                move.with_context({"force_delete": True}).unlink()
            rec.state = "cancelled"

class Inherit_account_payment(models.Model):
    _inherit = 'account.payment'

    status_saldo_budget = fields.Char()

class Inherit_account_analytic_line(models.Model):
    _inherit = 'account.analytic.line'

    status_saldo_budget = fields.Char()

class Inherit_account_move(models.Model):
    _inherit = 'account.move'

    cost_center = fields.Many2one('cost.center.child')
    status_saldo_budget = fields.Char()

class Inherit_account_move_line(models.Model):
    _inherit = 'account.move.line'

    cost_center = fields.Many2one('cost.center.child')
    status_saldo_budget = fields.Char()


class AccountPayment(models.Model):
    _inherit = "account.payment"

    expense_sheet_id = fields.Many2one(
        comodel_name="hr.expense.sheet", string="Expense sheet"
    )

class Inherit_cros_budget(models.Model):
    _inherit = 'crossovered.budget.lines'

    testing = fields.Char()
    grouping_id = fields.Many2one('account.analytic.group',compute='get_budget', store=True)
    grouping_ids = fields.Many2one('account.analytic.group',compute='get_budget')

    @api.depends('grouping_ids')
    def get_budget(self):
        for x in self.analytic_account_id.crossovered_budget_line:
            x.grouping_id = x.analytic_account_id.group_id
            x.grouping_ids = x.grouping_id


from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT

class CustomExpenseWizard(models.TransientModel):
    _name = 'custom.expense.report.wizard'

    date_start = fields.Date(string='Start Date',  default=lambda *a: datetime.today().date() + relativedelta(day=1))
    date_end = fields.Date(string='End Date', default=lambda *a: datetime.today().date() + relativedelta(day=31))

    def get_report(self):
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'date_start': self.date_start, 'date_end': self.date_end,
            },
        }

        # ref `module_name.report_id` as reference.
        return self.env.ref('expenses_request.custom_expense_report').report_action(self, data=data)



class ReportCustomReportView(models.AbstractModel):
    """
        Abstract Model specially for report template.
        _name = Use prefix `report.` along with `module_name.report_name`
    """
    _name = 'report.expenses_request.custom_expense_report_view'

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        docs = []
        docss = []

        sql="""select acc.name as budget,
            hr.analytic_account_id as budget_id from hr_expense hr
            join account_analytic_account acc on hr.analytic_account_id = acc.id
            where date >=%s and date <=%s
            group by hr.analytic_account_id,acc.name
            order by hr.analytic_account_id"""

        cr= self.env.cr
        cr.execute(sql,(date_start,date_end))
        result= cr.dictfetchall()
        for res in result:
            budget = res['budget']
            budget_id = res['budget_id']

            docss.append({
                'budget': budget,
                'budget_id': budget_id
                })
            docs = self.env['hr.expense'].search([
                ('date', '>=', date_start),
                ('date', '<=', date_end)])

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': date_start,
            'date_end': date_end,
            'docss': docss,
            'docs': docs
        }
# =================wizard department===============

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT

class CustomExpenseWizardDepartment(models.TransientModel):
    _name = 'custom.expense.report.wizard.department'

    @api.model    
    def _get_my_department(self):
        employees = self.env.user.employee_ids
        return (
            employees[0].department_id
            if employees
            else self.env["hr.department"] or False
        )

    department_id = fields.Many2one("hr.department", "Department", default=_get_my_department,required=True)
    date_start = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_end = fields.Date(string='End Date', required=True, default=fields.Date.today)

    def get_report_department(self):
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'date_start': self.date_start, 'date_end': self.date_end, 'department_id': self.department_id.id,
            },
        }

        # ref `module_name.report_id` as reference.
        return self.env.ref('expenses_request.custom_expense_report_department').report_action(self, data=data)



class ReportCustomReportViewDepartment(models.AbstractModel):
    """
        Abstract Model specially for report template.
        _name = Use prefix `report.` along with `module_name.report_name`
    """
    _name = 'report.expenses_request.custom_expense_report_view_department'

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        department_id = data['form']['department_id']
        docs = []
        docss = []

        sql="""select acc.name as budget,
            hr.analytic_account_id as budget_id from hr_expense hr
            join account_analytic_account acc on hr.analytic_account_id = acc.id
            where date >=%s and date <=%s and department_id =%s
            group by hr.analytic_account_id,acc.name
            order by hr.analytic_account_id"""

        cr= self.env.cr
        cr.execute(sql,(date_start,date_end,department_id))
        result= cr.dictfetchall()
        for res in result:
            budget = res['budget']
            budget_id = res['budget_id']

            docss.append({
                'budget': budget,
                'budget_id': budget_id
                })
            docs = self.env['hr.expense'].search([
                ('date', '>=', date_start),
                ('date', '<=', date_end)])

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': date_start,
            'date_end': date_end,
            'department_id': department_id,
            'docss': docss,
            'docs': docs

        }
# ========================new==========================

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT

class CustomExpenseWizardDepartmentA(models.TransientModel):
    _name = 'custom.expense.report.wizard.departmenta'

    department_id = fields.Many2one("account.analytic.group", "Department",required=True)
    date_start = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_end = fields.Date(string='End Date', required=True, default=fields.Date.today)

    def get_report_all_department(self):
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'date_start': self.date_start, 
                'date_end': self.date_end,
                'department_id': self.department_id.id,
            },
        }

        # ref `module_name.report_id` as reference.
        return self.env.ref('expenses_request.custom_expense_report_departmenta').report_action(self, data=data)



class ReportCustomReportViewDepartmentA(models.AbstractModel):
    """
        Abstract Model specially for report template.
        _name = Use prefix `report.` along with `module_name.report_name`
    """
    _name = 'report.expenses_request.custom_expense_report_view_departmenta'

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        department_id = data['form']['department_id']
        docs = []
        docss = []

        sql="""select aac.name as budget,
            cbl.analytic_account_id as budget_id,
            cbl.date_from as startdate,cbl.date_to as enddate from crossovered_budget_lines cbl
            join account_analytic_account aac on cbl.analytic_account_id = aac.id
            where group_id =%s 
            order by cbl.date_from,cbl.analytic_account_id"""

        cr= self.env.cr
        cr.execute(sql,(department_id,))
        result= cr.dictfetchall()
        for res in result:
            budget = res['budget']
            budget_id = res['budget_id']
            startdate = res['startdate']
            enddate = res['enddate']

            docss.append({
                'budget': budget,
                'startdate': startdate,
                'enddate': enddate,
                'budget_id': budget_id
                })
            docs = self.env['hr.expense'].search([
                ('date', '>=', date_start),
                ('date', '<=', date_end)])

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': date_start,
            'date_end': date_end,
            'department_id': department_id,
            'docss': docss,
            'docs': docs

        }