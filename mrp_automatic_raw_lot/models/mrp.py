"""File MRP"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    """class inherit mrp.production"""
    _inherit = 'mrp.production'

    def action_assign(self):
        ctx = dict(self.env.context)
        ctx['from_manufacture'] = True
        return super(MrpProduction, self.with_context(ctx)).action_assign()
