
import re

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero


class Inherit_hr_department(models.Model):
    _inherit = 'hr.department'

    dekan = fields.Many2one('res.users')
    warek = fields.Many2one('res.users')
    rektor = fields.Many2one('res.users')
    m_budget = fields.Many2one('res.users')
    corporate = fields.Many2one('res.users')
    ypk = fields.Many2one('res.users')
    approvals_line = fields.One2many('approvals.department','hr_id')


class ApprovalsDepartment(models.Model):
    _name = 'approvals.department'

    hr_id = fields.Many2one('inheriet.hr.department')
    amount_ap = fields.Selection([
        ("min_1jt", "Rp.1 s/d Rp.999.999"),
        ("min_10jt", "Rp.1.000.000 s/d Rp.9.999.999"),
        ("min_50jt", "Rp.10.000.000 s/d Rp.49.999.999"),
        ("max_50jt", "Rp.50.000.000 s/d ∞")])    
    manager_ap = fields.Boolean()
    dekan_ap = fields.Boolean()
    warek_ap = fields.Boolean()
    rektor_ap = fields.Boolean()
    m_budget_ap = fields.Boolean()
    corporate_ap = fields.Boolean()
    ypk_ap = fields.Boolean()





