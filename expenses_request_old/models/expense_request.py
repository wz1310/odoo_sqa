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

    department_id = fields.Many2one("hr.department", "Department",default=_get_my_department,
      required=True,readonly=True)
    sum_anggaran = fields.Selection([
        ('test1', 'Test 1'),
        ('test2', 'Test 2'),
        ('test3', 'Test 3')])
    target_keg = fields.Text()
    bank_names = fields.Many2one('account.journal', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Vendor',tracking=True)
    no_rek = fields.Integer(required=True,track_visibility="onchange")
    manager_id = fields.Many2one("hr.employee", "Manager",default=_get_my_manager,
      required=True,readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", readonly=True, store=True, default=_employee_get)
    kegiatan = fields.Char(track_visibility="onchange")
    tanggal_kegiatan = fields.Date(track_visibility="onchange")
    jumlah_dana = fields.Float(required=True,track_visibility="onchange")
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
    expense_count               = fields.Integer('Count',compute="compute_count")
    company_id                  = fields.Many2one('res.company', string='Company',
        required=True, readonly=True,
        default=lambda self: self.env.company)
    count_attachment = fields.Integer(compute='_compute_attachment', string="Berkas", track_visibility="onchange")
    products_id = fields.Many2one('product.product', domain="[('can_be_expensed', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    account_id = fields.Many2one('account.account', 
        string='Account', default=_default_account_id, 
        domain="[('internal_type', '=', 'other'), ('company_id', '=', company_id)]", 
        help="An expense account is expected")
    expense_line_ids = fields.One2many('expenses.request', 'expense_id', string='Expense Request Lines', copy=False)
