# -*- coding: utf-8 -*-
"""file res_users"""
from odoo import models, fields, api


class ResUsers(models.Model):
    """inherit models res users for add new field"""
    _inherit = 'res.users'

    branch_ids = fields.Many2many('res.branch', 'res_users_branch_rel',
        'user_id', 'branch_id', string='Allowed Operating Unit')
    #def_branch = fields.Many2one('branch', string='Branch')


    # @api.multi
    def write(self, vals):
        res = super(ResUsers, self).write(vals)
        if 'branch_ids' in vals:
            check = self.env.ref('base.res_company_rule_public')
            if check and check.perm_unlink:
                check.write({'perm_unlink': False})
            elif check and not check.perm_unlink:
                check.write({'perm_unlink': True})
        return res
