from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    region_group_id = fields.Many2one('region.group', string='Region Group')
    region_id = fields.Many2one('region.region', string="Region")
    region_master_id = fields.Many2one('region.master', string="Area", readonly=False)


    # @api.constrains('region_id','region_group_id')
    # def constrains_region_id(self):
    #     for rec in self:
    #         if (rec.region_id.id and not rec.region_group_id.id) or (rec.region_id.id and not rec.region_group_id.id != rec.region_id.


    @api.onchange('region_master_id')
    def _onchange_region_master_id(self):
        res = {
            'domain':{
                'region_group_id':[]
            }
        }
        if self.region_master_id.id:

            region_id = [('id','in',self.region_master_id.region_list_ids.ids)]
            res['domain'].update({
                'region_id':region_id,
                # 'region_group_id':[('id','in',self.region_master_id.region_list_ids.region_group_ids.ids)]
                })
        return res