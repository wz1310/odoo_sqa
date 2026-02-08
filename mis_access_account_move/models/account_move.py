# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError,RedirectWarning,AccessError
from datetime import datetime, timedelta, date

# class AccMoveLineInherrits(models.Model):
#     _inherit = 'account.move.line'
#     picking_id = fields.Many2one('stock.picking')

# ////////////////////////coba push lagi karena tidak terupdate di sistem/////////
class AccMoveInherrits(models.Model):
    _inherit = 'account.move'
    cek_user = fields.Boolean(string="check field", compute='cek_users')

    def cek_users(self):
        for x in self:
            x.cek_user = False
            if x.user_has_groups("mis_access_account_move.group_acess_qty_pfi"):
                x.cek_user = True
