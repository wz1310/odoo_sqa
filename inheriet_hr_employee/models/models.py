
import re

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero


class Inheriet_hr_employee(models.Model):
    _inherit = 'hr.employee'

    dekan = fields.Many2one('hr.employee')
    warek = fields.Many2one('hr.employee')
    rektor = fields.Many2one('hr.employee')