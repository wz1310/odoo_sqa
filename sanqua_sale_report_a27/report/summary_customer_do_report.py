from odoo import api, fields, models, tools
import logging
_logger = logging.getLogger(__name__)


class HargaDasarKonsumenReport(models.Model):
    _name = "report.summary.customer.do"
    _description = "Summary Customer DO Report"
    _auto = False
    _order = "id ASC"

    partner_id = fields.Many2one('res.partner', string='Customer')
    user_id = fields.Many2one('res.users', 'Salesperson', readonly=True)
    date = fields.Datetime('Order Date', readonly=True)
    product_uom_qty = fields.Float('Qty Ordered', readonly=True)
    price_total = fields.Float('Total Amount', readonly=True)
    untaxed_amount_invoiced = fields.Float('Paid', readonly=True)
    amount_residual = fields.Float('Amount Due', readonly=True)
    qty_to_deliver = fields.Float('Qty To Deliver', readonly=True)
    company_id = fields.Many2one('res.company', string='Company')
    top = fields.Many2one('account.payment.term',string='TOP',readonly=True)

    def get_main_request(self):
        request = """
            CREATE or REPLACE VIEW %s AS
                SELECT 
                    sr.id as id,
                    sr.partner_id,
                    sr.user_id,
                    sr.date,
                    sr.product_uom_qty,
                    sr.price_total,
                    sr.price_total - ABS(sr.amount_residual) as untaxed_amount_invoiced,
                    sr.qty_delivered - sr.product_uom_qty as qty_to_deliver,
                    sr.company_id,
                    so.payment_term_id as top,
                    sr.amount_residual
                FROM sale_report sr
                LEFT JOIN sale_order so ON so.id = sr.order_id
                LEFT JOIN account_payment_term apt ON apt.id = so.payment_term_id
                WHERE apt.name = 'DO' AND sr.state IN ('done','sale','forced_locked');
                """ % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())