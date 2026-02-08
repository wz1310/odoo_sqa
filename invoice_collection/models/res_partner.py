from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    collector = fields.Boolean(string='Collector',default=False, track_visibility='onchange')

    @api.constrains('collector')
    def _constrains_collector(self):
        for rec in self:
            if rec.collector == True and rec.employee != True:
                raise UserError(_('Non Employees are not allowed to be a collector!'))
    
    def btn_submit(self):
        self.ensure_one()
        if self.collector:
            self.update({'state':'approved', 'active':True})
        else:
            super().btn_submit()