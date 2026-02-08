from odoo import fields, models


class CrmTeam(models.Model):
    """Inherit crm team"""
    _inherit = 'crm.team'

    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms')
    product_category_ids = fields.Many2many('product.category')
