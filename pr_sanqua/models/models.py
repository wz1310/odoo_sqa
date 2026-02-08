import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero

class pr_sanqua(models.Model):
    _name = 'pr.sanqua'

    @api.model
    def _get_default_seq(self):
        return self.env["ir.sequence"].next_by_code("pr.sanqua.sequence")

    name = fields.Many2one('res.users', string='Request By')
    seq = fields.Char(default=_get_default_seq)
    date = fields.Date(string="Date")
    order_kategori = fields.Char(string="Order Kategori")
    created = fields.Date(string="Created On")
    asset = fields.Boolean(string="Asset")
    line_pr = fields.One2many('pr.sanqua.line','pr_id',string="PR Line")
    state = fields.Selection(selection=[
            ('draft', 'DRAFT'),
            ('to_approve', 'WAITING APPROVE')
            ,('approved','APPROVED')],string='Status',default='draft')
    seq_find = fields.Many2one('pr.sanqua', string='Request Num')


    @api.onchange('seq_find')
    def onchange_seq(self):
    	if self.seq_find:
    		cari = self.env['pr.sanqua'].search([])
    		self.seq_find = cari['seq']


    def create_po(self):
    	return{
    	'name': "Create PO",
    	'type': 'ir.actions.act_window',
    	'view_type': 'form',
    	'view_mode': 'form',
    	'res_model': 'pr.sanqua',
    	'view_id': self.env.ref('pr_sanqua.pr_sanqua_forms_view').id,
    	'target': 'new'
    	}

class pr_sanqua_line(models.Model):
    _name = 'pr.sanqua.line'

    name = fields.Many2one('product.product', string='Product')
    last_price = fields.Float(string="Last Price")
    price_total = fields.Float(string="Price Total")
    Description = fields.Char(string="Description")
    qty = fields.Float(string="Qty Released")
    uom = fields.Many2one('uom.uom')
    stock = fields.Char(string="Stock On Hand")
    incoming = fields.Char(string="Incoming")
    pr_id = fields.Many2one('pr.sanqua')
