from odoo import models, fields, api, _

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    safety_qty_alert_partner_ids = fields.Many2many('res.partner','company_partner_safety_stock_rel','company_id','partner_id', string="Safety Qty Alert Partner", related="company_id.safety_qty_alert_partner_ids",readonly=False)

class ResCompany(models.Model):
    _inherit = 'res.company'

    safety_qty_alert_partner_ids = fields.Many2many('res.partner','company_partner_safety_stock_rel','company_id','partner_id',string="Safety Qty Alert Partner")