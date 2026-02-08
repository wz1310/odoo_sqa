# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMoveDueDateFilter(models.Model):
    _name = 'account.move.due.date.filter'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Account Move Due Date Filter'

    name = fields.Char(string='Name', track_visibility='onchange')
    start_date = fields.Integer(string='Start Date',required=True, track_visibility='onchange')
    end_date = fields.Integer(string='End Date',required=True, track_visibility='onchange')
    active = fields.Boolean(string='Active',default=True, track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Compay',required=True,default=lambda self: self.env.company.id, track_visibility='onchange')

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, rec.name))
        return result