from odoo import fields, models, api, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    evaluasi_ids = fields.One2many('evaluasi.supplier', 'partner_id', string='Evaluasi')
    current_rating = fields.Integer()
