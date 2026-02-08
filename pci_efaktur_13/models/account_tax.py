
from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError

class AccountTax(models.Model):
    _inherit = 'account.tax'

    export_on_etax = fields.Boolean(string='Export On E-Tax',default=False, track_visibility='onchange')