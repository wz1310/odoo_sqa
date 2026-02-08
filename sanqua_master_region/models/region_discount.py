from odoo import api, fields, models, _

class RegionDiscount(models.Model):
    _name = 'region.discount'
    _description = "Region Discount"

    name = fields.Char(string='Name',required=True)
    region_group_id = fields.Many2one('region.group', string='Region Group',required=True)
    team_id = fields.Many2one('crm.team', string='Division', required=True)
    company_id = fields.Many2one('res.company', string='Company',required=True,default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    region_discount_product_ids = fields.One2many('region.discount.product', 'region_discount_id', string='Product Discount  per Wilayah')


    _sql_constraints = [
        ('region_team_company_unique', 'unique (region_group_id,team_id,company_id)', 'Region, Team, in same company must be unique'),
    ]