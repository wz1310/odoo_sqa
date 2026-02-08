from odoo import api, fields, models, _

class RegionGroup(models.Model):
    _name = 'region.group'
    _description = "Region Group"

    code = fields.Char(string='Code',required=True)
    name = fields.Char(string='Name',required=True)
    region_ids = fields.Many2many('region.region', 'region_group_region_region_rel','region_group_id', 'region_region_id' , string='Regions')
    company_id = fields.Many2one('res.company', string='Company',default=False,required=False)
    active = fields.Boolean(default=True)
    description = fields.Text(string='Description')

    _sql_constraints = [
        ('code_region_group_unique', 'unique(code,company_id)', 'code already exists!')
    ]


    def _read(self, fields):
        return super(RegionGroup, self.sudo())._read(fields)