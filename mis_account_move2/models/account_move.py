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

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    no_sj_wim = fields.Char(related="stock_move_id.picking_id.no_sj_wim", string="No SJ WIM")
    no_sj_plan = fields.Char(related="stock_move_id.picking_id.doc_name", string="No SJ Plan")
