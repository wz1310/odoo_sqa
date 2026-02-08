from odoo import api, fields, models, _

class RegionMaster(models.Model):
    _name = 'region.master'
    _description = "Region Master"

    name = fields.Char(string='Code Area',required=True)
    region_list_ids = fields.One2many('region.region', 'region_master_id', string='Regions')
