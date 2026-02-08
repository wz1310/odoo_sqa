# -*- coding: utf-8 -*-
"""file res_users"""
from odoo import models, fields, api


class ResUsers(models.Model):
    """inherit models res users for add new field"""
    _inherit = 'res.users'

    warehouse_ids = fields.Many2many('stock.warehouse', 'stock_warehouse_branch_rel',
        'warehouse_id', 'branch_id', string='Allowed Warehouse')

    # @api.multi
    def write(self, vals):
        res = super(ResUsers, self).write(vals)
        if 'warehouse_ids' in vals:
            check = self.env.ref('base.res_company_rule_public')
            if check and check.perm_unlink:
                check.write({'perm_unlink': False})
            elif check and not check.perm_unlink:
                check.write({'perm_unlink': True})
        return res
