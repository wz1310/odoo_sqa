import datetime
from odoo import fields,api,models,_

class MrpShift(models.Model):
    _name = 'mrp.shift'
    
    name = fields.Char(string='Name')
    responsible_id = fields.Many2one('res.users', string='Responsible/Pengawas', default=lambda x: x.env.user.id)
    create_date = fields.Datetime(string='Create Date', default=fields.Date.context_today)
    working_hours_start = fields.Float(string='Working Hours Start')
    working_hours_end = fields.Float(string='Working Hours End')
    working_hours_total = fields.Float(string='Working Hours Total', compute='_compute_total_hours', store=True)
    active = fields.Boolean(string='Active', default=True)
    code_shift = fields.Char()
    company_id = fields.Many2one('res.company', string='Plant')

    @api.depends('working_hours_start','working_hours_end')
    def _compute_total_hours(self):
    	if self.working_hours_start and self.working_hours_end:
            end = datetime.timedelta(hours=self.working_hours_end)
            start = datetime.timedelta(hours=self.working_hours_start)
            tot = end-start
            self.working_hours_total = tot.seconds/3600