from odoo import api, fields, models, _

class PartnerPricelist(models.Model):
    _inherit = 'partner.pricelist'

    customer_group = fields.Many2one('customer.group', string='Customer Group')
    payment_term_id = fields.Many2one('account.payment.term', string='Term of Payments')
    sales_admin_id = fields.Many2one('res.users')

    @api.onchange('team_id')
    def _onchange_team_id(self):
        return {'domain':{'sales_admin_id':[('id','in',self.team_id.sales_admin_ids.ids)]}}