# -*- coding: utf-8 -*-
"""file res_users"""
from odoo import models, fields, api


class ResUsers(models.Model):
    """inherit models res users for add new field"""
    _inherit = 'res.users'

    # sale_team_ids = fields.Many2many('crm.team', 'res_users_crm_team_rel',
    #     'user_id', 'team_id', string='Allowed Sales Team')
    sale_team_ids = fields.Many2many('crm.team', compute="_compute_sale_team_ids")
    #def_branch = fields.Many2one('branch', string='Branch')

    def _compute_sale_team_ids(self):
        # teams = self.env['crm.team']
        
        def find_team(user):
            Team = self.env['crm.team']
            teams = Team.search([])
            res = Team
            for team in teams:
                if user.id in team.member_ids.ids:
                    res+=team
            return res
        for rec in self:
            teams = find_team(rec)
            rec.sale_team_ids = teams

    # @api.multi
    def write(self, vals):
        res = super(ResUsers, self).write(vals)
        if 'sale_team_ids' in vals:
            check = self.env.ref('base.res_company_rule_public')
            if check and check.perm_unlink:
                check.write({'perm_unlink': False})
            elif check and not check.perm_unlink:
                check.write({'perm_unlink': True})
        return res
