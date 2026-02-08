from odoo import models, fields, api, _
from odoo.exceptions import UserError
from calendar import monthrange

class SalesUserTargetLine(models.Model):
    _inherit = 'sales.user.target.line'

    target_per_day = fields.Float(compute='_compute_target_per_day', string='Qty/Day',store=True)
    
    @api.depends('qty','target_id.month','target_id.hari_kerja')
    def _compute_target_per_day(self):
        for rec in self:
            # day_of_month = monthrange(int(rec.target_id.year), int(rec.target_id.month))[1]
            rec.target_per_day = rec.qty / rec.target_id.hari_kerja

