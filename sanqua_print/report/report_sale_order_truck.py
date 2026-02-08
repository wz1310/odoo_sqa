from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockDeliverySlipOnlyProduct(models.AbstractModel):
    _name = 'report.sanqua_print.report_sales_order_truck'
    _description = 'Report Sale Order Truck'

    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.order.truck'].browse(docids)
        for sot in docs:
            if sot.state not in ('confirmed', 'done'):
                raise UserError(_("You Only can print in state Confirmed and Done"))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'stock.order.truck',
            'docs': docs,
        }
