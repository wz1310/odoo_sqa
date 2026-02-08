from odoo import api, fields, models, _

class RegionRegion(models.Model):
    _name = 'region.region'
    _description = "Region"

    code = fields.Char(string='Region Code',required=False)
    name = fields.Char(string='Name',required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company',default=False)
    region_master_id = fields.Many2one('region.master', string='Code Area',required=False)

    region_group_ids = fields.Many2many('region.group','region_group_region_region_rel', 'region_region_id', 'region_group_id', string="Region Groups")

    _sql_constraints = [
        ('code_region_region_unique', 'unique(code,company_id)', 'code already exists!')
    ]

    def _read(self, fields):
        return super(RegionRegion, self.sudo())._read(fields)