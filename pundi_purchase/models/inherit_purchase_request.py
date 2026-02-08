# Copyright 2018-2019 ForgeFlow, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import _, api, fields, models
from odoo.exceptions import UserError

class Pundi_PurchaseRequest(models.Model):

    _inherit = "purchase.request"

    def _get_my_department(self):
        employees = self.env.user.employee_ids
        return (
            employees[0].department_id
            if employees
            else self.env["hr.department"] or False
        )

    department_id = fields.Many2one(
        "hr.department", "Department", default=_get_my_department,required=True
    )


    def _get_pr_mgr(self):
        employees = self.env.user.employee_ids
        # print(employees[0].pr_mgr.user_id)
        # exit();

        return (
            employees[0].pr_mgr.user_id
            if employees
            else self.env["res.users"] or False
        )

    assigned_to = fields.Many2one(
        comodel_name="res.users",
        string="Approver",
        track_visibility="onchange",
        default=_get_pr_mgr,
        required=True
    )

    @api.depends("state")
    def _compute_is_editable(self):
        # for rec in self:
        #     if rec.state in ("to_approve", "approved", "rejected", "done"):
        #         rec.is_editable = False
        #     else:
        #         rec.is_editable = True

        current_user = self.env['res.users'].browse(self.env.uid)
        for rec in self:
            if rec.state == 'draft' and current_user.has_group('purchase_request.group_purchase_request_user'):
                rec.is_editable = True
            elif rec.state == 'to_approve' and current_user.has_group('purchase_request.group_purchase_request_manager'):
                rec.is_editable = True
            # elif rec.state == 'manager_approved' and current_user.has_group('sprogroup_purchase_request.group_sprogroup_purchase_request_direktur'):
            #     rec.is_editable = True
            else:
                rec.is_editable = False

class Pundi_PurchaseRequestLine(models.Model):

    _inherit = "purchase.request.line"

    def _compute_is_editable(self):
        current_user = self.env['res.users'].browse(self.env.uid)
        for rec in self:
            # if rec.request_id.state in ("to_approve", "approved", "rejected", "done"):
            #     rec.is_editable = False

            if rec.request_id.state == 'draft' and current_user.has_group('purchase_request.group_purchase_request_user'):
                rec.is_editable = True
            elif rec.request_id.state == 'to_approve' and current_user.has_group('purchase_request.group_purchase_request_manager'):
                rec.is_editable = True
            else:
                rec.is_editable = False
        for rec in self.filtered(lambda p: p.purchase_lines):
            rec.is_editable = False