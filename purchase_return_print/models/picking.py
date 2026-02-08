from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'


    vendor_bill_to_ref_id = fields.Many2one('account.move', string="Vendor Bill Ref", domain=[('type','=','in_invoice')])
    available_vendor_bill_ids = fields.Many2many('account.move', string="Available Vendor Bills", compute="_compute_available_vendor_bill_ids")

    def _compute_available_vendor_bill_ids(self):
        for rec in self:
            moves = self.env['account.move']
            if rec.purchase_id.id:
                moves = rec.purchase_id.invoice_ids
            rec.available_vendor_bill_ids = [(6,0,moves.ids)]
