from odoo import api, fields, models, _

class ResPartnerCompetitor(models.Model):
    _inherit = 'res.partner'

    competitor_ids = fields.One2many('res.partner.competitor', 'partner_id', string='Competitor')