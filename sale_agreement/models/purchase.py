"""File Purchase Order"""
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    """class inherit purchase.order"""
    _inherit = "purchase.order"

    sale_agreement_id = fields.Many2one('sale.agreement',
        string='Sale Agreement Reference', copy=False)

    @api.onchange('sale_agreement_id')
    def _onchange_sale_agreement_id(self):
        if not self.sale_agreement_id:
            return
        agreement = self.sale_agreement_id
        if not self.origin or agreement.name not in agreement.origin.split(', '):
            if self.origin:
                if agreement.name:
                    self.origin = self.origin + ', ' + agreement.name
            else:
                self.origin = agreement.name
        date_order = fields.Datetime.now()
        if date_order.date() > agreement.end_date:
            date_order = datetime.strptime(agreement.end_date,
                '%Y-%m-%d').strftime('%Y-%m-%dT%H:%M:%S.%f')
        elif date_order.date() < agreement.start_date:
            date_order = datetime.strptime(agreement.start_date,
                '%Y-%m-%d').strftime('%Y-%m-%dT%H:%M:%S.%f')
        self.date_order = date_order
        self.user_id = agreement.user_id.id
        self.company_id = agreement.company_id.id
        self.currency_id = agreement.currency_id.id
        # Create PO lines if necessary
        order_lines = []
        for line in agreement.agreement_line_ids:
            # Compute taxes
            taxes_ids = line.product_id.supplier_taxes_id.filtered(
                lambda tax: tax.company_id == agreement.company_id).ids
            # Create PO line
            line_values = {
                'name': line.product_id.display_name,
                'product_id': line.product_id.id,
                'product_uom': line.product_id.uom_po_id.id,
                'product_qty': line.product_qty,
                'price_unit': 0.0,
                'taxes_id': [(6, 0, taxes_ids)],
                'date_planned': date_order,
            }
            order_lines.append((0, 0, line_values))
        self.order_line = order_lines
