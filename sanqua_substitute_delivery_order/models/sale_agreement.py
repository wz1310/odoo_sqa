from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class SaleAgreementLine(models.Model):
    _inherit = 'sale.agreement.line'

    @api.depends('agreement_id.sale_order_ids', 'agreement_id.sale_order_ids.state', 'product_qty')
    def _compute_qty_so(self):
        for line in self:
            qty_product_in_so = line.agreement_id.sale_order_ids.filtered(lambda so:so.state in\
                ('sale', 'done')).mapped('order_line').filtered(lambda x: x.product_id.id == line.product_id.id and x.order_id.substitute_with_order_id.id==False)
            tota_per_product = sum(so.product_uom_qty for so in qty_product_in_so)
            line.product_qty_sale_order = tota_per_product
            line.remaining_qty = line.product_qty - line.product_qty_sale_order