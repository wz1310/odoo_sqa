from odoo import fields,api,models,_

class Reason(models.Model):
    _name = 'reason'
    
    name = fields.Char(string='Name')
    