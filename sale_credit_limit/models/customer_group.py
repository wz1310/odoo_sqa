from odoo import api, fields, models, _

class CustomerGroup(models.Model):
    _name = 'customer.group'

    name = fields.Char(string='Name',required=True)
    active = fields.Boolean(default=True)