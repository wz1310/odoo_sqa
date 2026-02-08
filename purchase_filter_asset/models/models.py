
from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError


class purchase_filter_asset(models.Model):
    _inherit = 'purchase.request'

    filter_asset = fields.Boolean(compute='find_filter')
    user_sanqua = fields.Char(string='User eSanqua')
    no_fpb_sanqua = fields.Char(string='No.FPB')

    def find_filter(self):
        if any([p.is_asset == True for p in self.line_ids.product_id]):
            self.is_asset = True
            self.filter_asset = True
        else:
            self.filter_asset = False
            self.is_asset = False

    @api.onchange('is_asset')
    def onchanges_is_ast(self):
        if any([p.is_asset == True for p in self.line_ids.product_id]):
            self.is_asset = True
            raise UserError(_("Ada produk asset!!"))

    @api.onchange('purchase_order_type')
    def onchanges_purchase_order_type(self):
        if self.purchase_order_type == 'asset':
            self.is_asset = True