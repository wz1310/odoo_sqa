from odoo import fields,api,models,_

class CrmTeam(models.Model):
    _inherit = 'crm.team'
    
    product_category_ids = fields.Many2many('product.category', string="Allowed Product Categories")