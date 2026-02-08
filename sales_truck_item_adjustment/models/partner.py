from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    sale_truck_adjustment_ids = fields.One2many('sales.truck.item.adjustment', 'partner_id', string='Deposito Galon', domain=[('adjustment_type', '=', 'deposit'), ('state', '=', 'done')])
    deposito_amount = fields.Monetary(compute='_compute_deposito_amount', string='Deposito Amount')
    
    @api.depends('sale_truck_adjustment_ids')
    def _compute_deposito_amount(self):
        for rec in self:
            rec.deposito_amount = sum([x.amount for x in rec.sale_truck_adjustment_ids if x.state == 'done'])