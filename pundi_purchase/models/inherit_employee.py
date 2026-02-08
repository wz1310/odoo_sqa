# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from ast import literal_eval

from odoo import api, fields, models
from pytz import timezone, UTC
from odoo.tools import format_time


class pundi_purchase_HrEmployee(models.Model):
    _inherit = "hr.employee"
    pr_mgr = fields.Many2one('hr.employee', 'PR Manager', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

class pundi_purchase_HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"
    pr_mgr = fields.Many2one('hr.employee.public', 'PR Manager', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")