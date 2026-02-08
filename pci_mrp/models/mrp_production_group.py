import datetime
from odoo import fields,api,models,_

class MrpProductionGroup(models.Model):
    _name = 'mrp.production.group'
    
    name = fields.Char(string='Name')
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 readonly=True, index=True, default=lambda self: self.env.company)
    group_leader_id = fields.Many2one('res.users','Leader')
    member_ids = fields.Many2many('res.users')

