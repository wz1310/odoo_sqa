# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero


class Expenses_Sheet(models.Model):
    _name = 'expenses.sheet'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Expenses Sheet"
    _order = "id desc"

    @api.model
    def _employee_get(self):
      record = self.env['hr.employee'].search([('user_id', '=', self.env.user.login)]) 
      return record[0]

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
    name = fields.Char(track_visibility="onchange")
    tanggal_kegiatan = fields.Date(track_visibility="onchange")
    jumlah_dana = fields.Float(track_visibility="onchange")
    atas_nama = fields.Char(string="Atas nama")
    status_anggaran = fields.Selection([
        ('ada', 'Ada'),
        ('tidak_ada', 'Tidak Ada')])
    expense_id                  = fields.Many2one('hr.expense', string="Expense Id")
    company_id                  = fields.Many2one('res.company', string='Company',
        required=True, readonly=True,
        default=lambda self: self.env.company)
    products_id = fields.Many2one('product.product', domain="[('can_be_expensed', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    account_id = fields.Many2one('account.account', 
        string='Account', default=_default_account_id, 
        domain="[('internal_type', '=', 'other'), ('company_id', '=', company_id)]", 
        help="An expense account is expected")
    expenses_request_line = fields.One2many(comodel_name="expenses.request",
        inverse_name="expenses_request_id",string="Expense Request Sheet",
        readonly=False,copy=True,track_visibility="onchange",)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', check_company=True)

    @api.onchange('products_id', 'company_id')
    def _onchange_product_id(self):
        if self.products_id:
            account = self.products_id.product_tmpl_id._get_product_accounts()['expense']
            self.account_id = account