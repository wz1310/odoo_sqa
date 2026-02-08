from odoo import api, fields, models, _

class ProductGroup(models.Model):
    _name = 'product.group'
    _description = "Product Group"

    name = fields.Char(string='Name',required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
    ('name_group_unique', 'unique(name)', 'name already exists!')
]

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_group_id = fields.Many2one('product.group', string='Product Group')