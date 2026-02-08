# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero

_STATES = [
   ("draft", "Draft"),
    ("submit", "To be approved"),
    # ("confirm", "Approved"),
    # ("validate", "Validate"),
    ("done", "Done"),
    ("cancel", "Cancel"),
    ]

# _STATUS = [
#    ("wait_direktur", "Wait Direktur"),
#    ("wait_gm", "Wait General Manager"),
#     ("wait_manager_direktur", "Wait Manager Direktur"),
#     ]
class Expenses_Request(models.Model):
    _name = 'expenses.request'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Expenses Request"
    _order = "id desc"

    def action_create_sheet(self):
        todo = self.filtered(lambda x: x.payment_mode=='own_account') or self.filtered(lambda x: x.payment_mode=='company_account')
        sheet = self.env['hr.expense.sheet'].create({
            'company_id': self.company_id.id,
            'employee_id': self[0].employee_id.id,
            'name': todo[0].name if len(todo) == 1 else '',
            'expense_line_ids': [(6, 0, todo.ids)]
        })
        sheet._onchange_employee_id()

    @api.model
    def _employee_get(self):
      record = self.env['hr.employee'].search([('user_id', '=', self.env.user.login)]) 
      return record[0]

    @api.model
    def _get_default_name(self):
        return self.env["ir.sequence"].next_by_code("expenses.request")

    def _get_my_department(self):
        employees = self.env.user.employee_ids
        return (
            employees[0].department_id
            if employees
            else self.env["hr.department"] or False
        )

    def _get_my_manager(self):
        employees = self.env.user.employee_ids
        return (
            employees[0].parent_id
            if employees
            else self.env["hr.employee"] or False
        )

    def _default_account_id(self):
        return self.env['ir.property'].get('property_account_expense_categ_id', 'product.category')

    department_id = fields.Many2one("hr.department", "Department",default=_get_my_department,
      required=True,readonly=True)
    sum_anggaran = fields.Selection([
        ('test1', 'Test 1'),
        ('test2', 'Test 2'),
        ('test3', 'Test 3')])
    target_keg = fields.Text()
    bank_names = fields.Many2one('account.journal', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Vendor',tracking=True)
    no_rek = fields.Integer(track_visibility="onchange")
    manager_id = fields.Many2one("hr.employee", "Manager",default=_get_my_manager,
      required=True,readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", readonly=True, store=True, default=_employee_get)
    kegiatan = fields.Char(required=True,track_visibility="onchange")
    tanggal_kegiatan = fields.Date(required=True,track_visibility="onchange")
    jumlah_dana = fields.Float(track_visibility="onchange")
    unit_amount = fields.Float("Unit Price", required=True, digits='Product Price')
    quantity = fields.Float(required=True, digits='Product Unit of Measure', default=1)
    tax_ids = fields.Many2many('account.tax', domain="[('company_id', '=', company_id), ('type_tax_use', '=', 'purchase')]", string='Taxes')
    untaxed_amount = fields.Float("Subtotal", store=True, compute='_compute_amount', digits='Account')
    atas_nama = fields.Char(string="Atas nama")
    status_anggaran = fields.Selection([
        ('ada', 'Ada'),
        ('tidak_ada', 'Tidak Ada')])
    state = fields.Selection(
        selection=_STATES,
        string="Status",
        index=True,
        track_visibility="onchange",
        required=True,
        copy=False,
        default="draft",
    )

    is_editable = fields.Boolean(
        string="Is editable", compute="_compute_is_editable", readonly=True)

    status = fields.Selection(selection=[
            ('wait_manager', 'Wait For Manager Approve'),
            ('wait_general_manager', 'Wait For General Manager Approve'),
            ('wait_direktur', 'Wait For Direktur Approve'),
            ('wait_manager_direktur', 'Wait For Manager Direktur Approve')],
            string='Status',track_visibility="onchange")

    deskripsi_approve           = fields.Char(string="Approve By", readonly=True)
    expense_id                  = fields.Many2one('hr.expense', string="Expense Id")
    referensi                   = fields.Char(readonly = True)   
    approve_mg                  = fields.Boolean('Approve Manager')
    approve_gm                  = fields.Boolean('Approve General Manager')
    approve_direktur            = fields.Boolean('Approve Direktur')
    approve_manager_direktur    = fields.Boolean('Approve Managing Direktur')
    total_amount                = fields.Monetary("Total", compute='_compute_amount', store=True, currency_field='currency_id')
    expense_count               = fields.Integer('Count')
    company_id                  = fields.Many2one('res.company', string='Company',
        required=True, readonly=True,
        default=lambda self: self.env.company)
    count_attachment = fields.Integer(compute='_compute_attachment', string="Berkas", track_visibility="onchange")
    product_id = fields.Many2one('product.product',required=True, domain="[('can_be_expensed', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    account_id = fields.Many2one('account.account', 
        string='Account', default=_default_account_id, 
        domain="[('internal_type', '=', 'other'), ('company_id', '=', company_id)]", 
        help="An expense account is expected")
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', check_company=True, required=True)
    payment_mode = fields.Selection([("own_account", "Employee (to reimburse)"),("company_account", "Company")
    ], default='company_account',string="Paid By",)
    totals = fields.Float()
    expenses_request_id = fields.Many2one(
        comodel_name="expenses.sheet",
        string="Expenses Request",
        ondelete="cascade",
        readonly=True,)
    exp_request_id = fields.Many2one(
        comodel_name="hr.expense.sheet",
        string="Exp Request")
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, default=lambda self: self.env.company.currency_id)

    @api.depends('quantity', 'unit_amount', 'tax_ids', 'currency_id')
    def _compute_amount(self):
        for expense in self:
            expense.untaxed_amount = expense.unit_amount * expense.quantity
            taxes = expense.tax_ids.compute_all(expense.unit_amount, expense.currency_id, expense.quantity, expense.product_id, expense.employee_id.user_id.partner_id)
            expense.total_amount = taxes.get('total_included')

    @api.onchange('product_id', 'company_id')
    def _onchange_product_id(self):
        if self.product_id:
            account = self.product_id.product_tmpl_id._get_product_accounts()['expense']
            self.account_id = account
            self.tax_ids = [(6,0, self.product_id.taxes_id.ids)]

    def _compute_attachment(self):
        for employee in self:
            employee.count_attachment = self.env['ir.attachment'].search_count([
                ('res_model', '=', employee._name),
                ('res_id', '=', employee.id),])

    # def compute_total(self):
    #     for order in self:
    #         line_total = 0.0
    #         for line in order.expenses_request_line:
    #             line_total += line.jumlah_dana
    #         order.total = line_total
    #         order.write({'totals': line_total})

    def action_view_employee_attachment(self):
        return{
        'name': 'Attachment',
        'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
        'res_model': 'ir.attachment',
        'type': 'ir.actions.act_window',
        'view_mode': 'kanban,tree,form',
        'view_type': 'form',
        'limit': 80,
        'context': {
        'default_res_model': self._name,
        'default_res_id': self.id,
        }
        }

    def act_post(self):
        # nominal = self.jumlah_dana
        nominal = self.total
        if nominal <= 1000000:
            self.approve_mg = True
            self.approve_gm = False
            self.approve_direktur = False
            self.approve_manager_direktur = False
            self.write({"state": "submit"})
            self.deskripsi_approve = "Manager"
        elif((nominal > 1000001) and (nominal <= 5000000)):
            self.approve_mg = True
            self.approve_gm = True
            self.approve_direktur = False
            self.approve_manager_direktur = False
            self.write({"state": "submit"})
            self.deskripsi_approve = "Manager > General Manager"
        elif ((nominal > 5000001) and (nominal < 10000000)):
            self.approve_mg = True
            self.approve_gm = True
            self.approve_direktur = True
            self.approve_manager_direktur = False
            self.write({"state": "submit"})
            self.deskripsi_approve = "Manager > General Manager > Direktur"
        elif nominal > 10000001:
            self.approve_mg = True
            self.approve_gm = True
            self.approve_direktur = True
            self.approve_manager_direktur = True
            self.write({"state": "submit"})
            self.deskripsi_approve = "Manager > General Manager > Direktur > Managing Direktur"

    @api.depends("state")           
    def _compute_is_editable(self):
        for rec in self:
            if rec.state in ("submit", "done", "cancel"):
                rec.is_editable = False
                self.write({"referensi": self.name})
            else:
                rec.is_editable = True
                self.write({"referensi": self.name})

    name = fields.Char(
        string="Request Reference",
        required=True,
        default=_get_default_name,
        track_visibility="onchange",
        )

    def act_approve_mg(self):
        nominal = self.total
        if ((nominal > 0) and (nominal <= 1000000)):
            self.state = 'done'
            self.deskripsi_approve = "Done"
            self.approve_mg = False
            self.approve_gm = False
            self.approve_direktur = False
            self.approve_manager_direktur = False
            # self.env.cr.execute(""" SELECT  MAX(s.id) AS no_max FROM expenses_sheet s """,())
            # get_no_max  = self.env.cr.dictfetchall()
            # sequence = 1
            # for data in get_no_max :
            #     if data['no_max'] :
            #         sequence = int(data['no_max']) + 1
            Expense_SheetCreate = self.env['hr.expense.sheet'].create(
                                                                        { 
                                                                            # 'id'          : sequence,
                                                                            'name'        : self.name,
                                                                            'employee_id' : self.employee_id.id,
                                                                            'expense_request_id' : self.id,
                                                                            # 'company_id'  : self.company_id.id,
                                                                            'total_amount'  : self.total,
                                                                            # 'state'       : 'draft'
                                                                        }
                                                                    ) 

                    # expense_sheets = self.env['expenses.sheet'].search([('expenses_request_id', '=', self.id)])
                    # for sheets_lines in expense_sheets:
                    #     ExpenseCreate = self.env['hr.expense'].create({ 
                    #                                                 'name'                  : sheets_lines.name,
                    #                                                 'date'                  : self.tanggal_kegiatan,
                    #                                                 'employee_id'           : self.employee_id.id,
                    #                                                 'state'                 : 'draft',
                    #                                                 'product_id'            : self.products_id.id,
                    #                                                 'product_uom_id'        : 1,
                    #                                                 'unit_amount'           : 1,
                    #                                                 'quantity'              : 1,
                    #                                                 'total_amount'          : self.total,
                    #                                                 'company_id'            : self.company_id.id,
                    #                                                 'analytic_account_id'   : self.analytic_account_id.id,
                    #                                                 'account_id'            : self.account_id.id,
                    #                                                 'payment_mode'          : self.payment_mode,
                    #                                                 'sheet_id'              : Expense_SheetCreate.id,
                    #                                                 'attachment_number'     : self.count_attachment}
                    #                                                 ) 
                    
                # else:
                    # sequence = 1
                    # ExpenseCreate = self.env['hr.expense'].create({ 'id':sequence, 'name':
                    #   self.kegiatan, 'employee_id': self.employee_id.id, 'unit_amount':
                    #   self.jumlah_dana, 'company_id': 1, 'state': 'draft'}
                    #   )
                    # self.state = 'submit'
        elif self.deskripsi_approve == "Manager > General Manager":
            self.approve_mg = False
            self.status = 'wait_general_manager'

    def act_approve_gm(self):
        nominal = self.jumlah_dana
        if ((nominal > 1000001) and (nominal <= 5000000)):
            self.deskripsi_approve = "Done"
            self.approve_gm = False
            self.approve_direktur = False
            self.approve_manager_direktur = False
            self.env.cr.execute(""" SELECT  MAX(s.id) AS no_max FROM expenses_request s """,())
            get_no_max  = self.env.cr.dictfetchall()
            sequence = 1
            for data in get_no_max :
                if data['no_max'] :
                    sequence = int(data['no_max']) + 1
                    ExpenseCreate = self.env['hr.expense'].create({ 'id':sequence, 'name':
                        self.kegiatan, 'employee_id': self.employee_id.id, 'unit_amount':
                        self.jumlah_dana, 'company_id': 1,'account_id': self.account_id.id, 'expense_reg_id' : self.id ,'product_id': self.product_id.id , 'attachment_number' : self.count_attachment,'state': 'draft'}
                        )
                    self.expense_id = ExpenseCreate.id
                    self.state = 'done'
                else:
                    # sequence = 1
                    # ExpenseCreate = self.env['hr.expense'].create({ 'id':sequence, 'name':
                    #   self.kegiatan, 'employee_id': self.employee_id.id, 'unit_amount':
                    #   self.jumlah_dana, 'company_id': 1, 'state': 'draft'}
                    #   )
                    self.state = 'submit'
        elif(self.deskripsi_approve,'=',"Manager > General Manager > Direktur"):
            self.approve_gm = False
            self.status = 'wait_direktur'

    def act_approve_dir(self):
        nominal = self.jumlah_dana
        if ((nominal > 5000001) and (nominal < 10000000)):
            self.deskripsi_approve = "Done"
            self.approve_direktur = False
            self.env.cr.execute(""" SELECT  MAX(s.id) AS no_max FROM expenses_request s """,())
            get_no_max  = self.env.cr.dictfetchall()
            sequence = 1
            for data in get_no_max :
                if data['no_max'] :
                    sequence = int(data['no_max']) + 1
                    ExpenseCreate = self.env['hr.expense'].create({ 'id':sequence, 'name':
                        self.kegiatan, 'employee_id': self.employee_id.id, 'unit_amount':
                        self.jumlah_dana, 'company_id': 1,'account_id': self.account_id.id, 'expense_reg_id' : self.id ,'product_id': self.product_id.id , 'attachment_number' : self.count_attachment,'state': 'draft'}
                        )
                    self.expense_id = ExpenseCreate.id
                    self.state = 'done'
                else:
                    # sequence = 1
                    # ExpenseCreate = self.env['hr.expense'].create({ 'id':sequence, 'name':
                    #   self.kegiatan, 'employee_id': self.employee_id.id, 'unit_amount':
                    #   self.jumlah_dana, 'company_id': 1, 'state': 'draft'}
                    #   )
                    self.state = 'submit'
        elif(self.deskripsi_approve,'=',"Manager > General Manager > Direktur > Managing Direktur"):
            self.approve_direktur = False
            self.status = 'wait_manager_direktur' 

    def act_approve_man_dir(self):
        self.deskripsi_approve = "Done"
        self.approve_manager_direktur = False
        self.env.cr.execute(""" SELECT  MAX(s.id) AS no_max FROM expenses_request s """,())
        get_no_max  = self.env.cr.dictfetchall()
        sequence = 1
        for data in get_no_max :
            if data['no_max'] :
                sequence = int(data['no_max']) + 1
                ExpenseCreate = self.env['hr.expense'].create({ 'id':sequence, 'name':
                        self.kegiatan, 'employee_id': self.employee_id.id, 'unit_amount':
                        self.jumlah_dana, 'company_id': 1,'account_id': self.account_id.id, 'expense_reg_id' : self.id ,'product_id': self.product_id.id , 'attachment_number' : self.count_attachment,'state': 'draft'}
                        )
                self.expense_id = ExpenseCreate.id
                self.state = 'done'
            else:
                # sequence = 1
                # ExpenseCreate = self.env['hr.expense'].create({ 'id':sequence, 'name':
                #   self.kegiatan, 'employee_id': self.employee_id.id, 'unit_amount':
                #   self.jumlah_dana, 'company_id': 1, 'state': 'draft'}
                #   )
                self.state = 'submit'

    def get_expense(self):
        self.ensure_one()
        return {
            'type'          : 'ir.actions.act_window',
            'name'          : 'Expense',
            'view_mode'     : 'tree,form',
            'res_model'     : 'hr.expense.sheet',
            'context'       : {'default_expense_request_id':self.id},
            'domain'        : [('expense_request_id', '=', self.id)]
        }

    # def compute_count(self):
    #     for record in self:
    #         record.expense_count = self.env['hr.expense.sheet'].search_count(
    #             [('expense_request_id', '=', self.id)])

    def copy(self, default=None):
        default = dict(default or {})
        self.ensure_one()
        default.update(
            {
                "state": "draft",
                "name": self.env["ir.sequence"].next_by_code("expenses.request"),
            }
        )
        return super(Expenses_Request, self).copy(default)

    # def action_create_sheet(self):
    # 	sheet = self._create_sheet()
    # 	return {
    # 	'name': _('New Expense Report'),
    # 	'type': 'ir.actions.act_window',
    # 	'view_mode'	: 'form',
    # 	'res_model'	: 'expenses.sheet',
    # 	'target'	: 'current',
    # 	'res_id'	: sheet.id,
    # 	}
    # def _create_sheet(self):
    # 	sheet = self.env['expenses.sheet'].create({
    # 		'name': self.name,
    # 		'employee_id': self.employee_id.id,
    # 		'company_id': self.company_id.id,
    # 		'kegiatan': self.kegiatan,
    # 		})
    # 	return sheet



        