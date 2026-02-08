from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError

class ResCompany(models.Model):
    _inherit = 'res.company'

    default_discount_support_journal_id = fields.Many2one('account.journal', string='Default Journal Discount Support')
    default_discount_target_journal_id = fields.Many2one('account.journal', string='Default Journal Discount Target')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    discount_support_journal_id = fields.Many2one('account.journal', related='company_id.default_discount_support_journal_id', string='Journal Discount Support', readonly=False)
    discount_target_journal_id = fields.Many2one('account.journal', related='company_id.default_discount_target_journal_id', string='Journal Discount Target', readonly=False)
