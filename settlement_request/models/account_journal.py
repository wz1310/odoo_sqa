from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_down_payment = fields.Boolean(string='Is Down Payment?')
    payment_category = fields.Selection([
        ('cek', 'Cek/Giro'),
        ('cash', 'Cash')
    ], string='Payment')