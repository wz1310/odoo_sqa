# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _description = 'Purchase Request'
    _inherit = ["approval.matrix.mixin", 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Reference", required=True,
                       track_visibility='onchange', default="New")
    date_order = fields.Datetime(
        string='Date', track_visibility='onchange', default=lambda self: self._default_date())
    user_id = fields.Many2one('res.users', string='Request By', required=True,
                              track_visibility='onchange', default=lambda self: self.env.user)
    employee_id = fields.Many2one(
        'hr.employee', compute='_compute_employee_id', track_visibility='onchange')
    department_id = fields.Many2one(
        related='employee_id.department_id', track_visibility='onchange')
    is_asset = fields.Boolean(
        string='Asset', default=False, track_visibility='onchange')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval', 'Waiting Approval'),
        ('rejected', 'Reject'),
        ('approved', 'Approved'),
        ('purchase_order', 'Purchase Order')
    ], string='State', default='draft', required=True, track_visibility='onchange')
    line_ids = fields.One2many('purchase.request.line', 'purchase_request_id',
                               string='Purchase Request Line', track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id, track_visibility='onchange')

    purchase_ids = fields.Many2many(
        'purchase.order', compute="_compute_purchase_ids", string="Purchases", compute_sudo=True)
    purchase_ids_count = fields.Integer(
        compute="_compute_purchase_ids_count", string="PO Count")
    purchase_order_type = fields.Selection([('bahan_baku', 'PO BAHAN BAKU PRODUKSI'),
                                            ('bahan_pendukung',
                                             'PO BAHAN PENDUKUNG PRODUKSI'),
                                            ('asset', 'PO ASSET'),
                                            ('barang_khusus', 'PO BARANG KHUSUS'),
                                            ('operasional', 'PO OPERATIONAL'),
                                            ('amdk', 'PO AMDK & BVG '),
                                            ('lain', 'PO LAIN LAIN')
                                            ], string="Order Kategori")
    status_pr = fields.Selection(
        [("open", "In Progress"), ("done", "Done"), ("close", "Close")], default='open')

    def btn_close(self):
        self.status_pr = 'close'

    def open_po(self):
        self.ensure_one()

        context = dict(self.env.context or {})
        # context.update({}) #uncomment if need append context
        res = {
            'name': "%s" % (_('Purchase Orders')),
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'view_ids': [(False, 'tree'), (False, 'form')],
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'current',
            'domain': [('id', 'in', self.purchase_ids.ids)]
        }
        return res

    def _compute_purchase_ids_count(self):
        for rec in self:
            rec.purchase_ids_count = len(rec.purchase_ids)

    _sql_constraints = [
        ('name_unique', 'unique (name)', 'Name must be unique'),
    ]

    def _default_date(self):
        return fields.Datetime.now()

    @api.depends('line_ids.purchase_line_ids')
    def _compute_purchase_ids(self):
        for rec in self:
            purchases = rec.line_ids.mapped(
                lambda r: r.purchase_line_ids.mapped('order_id'))
            rec.purchase_ids = purchases

    def _fetch_next_seq(self):
        return self.env['ir.sequence'].next_by_code('seq.purchase.request')

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        return super().copy(default={
            'name': 'New',
        })

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            if val.get('name') == False or val.get('name').lower() == 'new':
                val.update({'name': self._fetch_next_seq()})

        return super().create(vals)

    @api.depends('user_id')
    def _compute_employee_id(self):
        self.employee_id = self.user_id.employee_id
        if not self.employee_id:
            # raise UserError(_("%s employee's data not found!Please contact system administrator!") % (self.user_id.display_name))
            pass

    def open_po_wizard(self):
        form = self.env.ref(
            'purchase_request.purchase_request_to_order_wizard_form', raise_if_not_found=False)
        return {
            'name': _('Create Purchase Order'),
            'type': 'ir.actions.act_window',

            'view_mode': 'form',
            'res_model': 'purchase.request.to.order',
            'views': [(form.id, 'form')],
            'view_id': form.id,
            'target': 'new',
            'context': {
                    '_default_request_id': self.id
            },
        }

    def btn_draft(self):
        self.state = 'draft'

    def validate_department(self):
        self.ensure_one()
        if not len(self.user_id.employee_ids):
            # raise UserError(_("User %s doesnt have any Employee Data. Please Tell System Administrator!") % (self.user_id.display_name,))
            pass

    def validate_item(self):
        self.ensure_one()
        if len(self.line_ids) == 0:
            raise UserError(_("Please fill item(s) to request!"))

    def btn_submit(self):
        self.validate_item()
        self.validate_department()
        self.checking_approval_matrix(add_approver_as_follower=True, data={
                                      'state': 'waiting_approval'})

    def btn_reject(self):
        self.rejecting_matrix()
        self.state = 'rejected'
        self.line_ids.reject()

    def open_reject_message_wizard(self):
        self.ensure_one()

        form = self.env.ref('approval_matrix.message_post_wizard_form_view')
        context = dict(self.env.context or {})
        context.update({'default_prefix_message': "<h4>Rejecting Purchase Request</h4>",
                       "default_suffix_action": "btn_reject"})  # uncomment if need append context
        context.update({'active_id': self.id, 'active_ids': self.ids,
                       'active_model': 'purchase.request'})
        res = {
            'name': "%s - %s" % (_('Rejecting Purchase Request'), self.name),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'message.post.wizard',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res

    def action_approve(self):
        self.state = 'approved'
        self.line_ids.approve()

    def btn_approve(self):
        self.approving_matrix(post_action='action_approve')

    # Created by : SanQua
    # At: 16/09/2021
    # Purpose: To make force select of 'Order Kategori' become 'asset' when user check 'asset' checkbox
    @api.onchange('is_asset')
    def _on_change_is_asset(self):
        print('>>> Is Asset : ' + str(self.is_asset))
        if self.is_asset:
            self.purchase_order_type = 'asset'

        else:
            self.purchase_order_type = ''
