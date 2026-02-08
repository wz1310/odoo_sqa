from odoo import api, fields, models, tools
import logging
from datetime import datetime
_logger = logging.getLogger(__name__)


class PerformaCustomerReport(models.Model):
    _name = "report.performa.customer"
    _description = "Performa Customer Report"
    _auto = False
    _order = "id"
    
    year = fields.Char(string='Year')
    month = fields.Char(string='Month')
    ref = fields.Char(string='Sales ID')
    user_id = fields.Many2one('res.users', string='Salesman')
    partner_code = fields.Char(string='Customer Code')
    partner_name = fields.Char(string='Customer')
    partner_id = fields.Many2one('res.partner', string='Partner ID')
    region_master_id = fields.Many2one('region.master', string='Area')
    customer_group_id = fields.Many2one('customer.group',string='Class Outlet')
    pricelist_id = fields.Many2one('partner.pricelist')
    invoice_90 = fields.Float(string='Piutang Lebih dari 90 Hari')
    payment = fields.Float(string='Penjualan')
    payment_unpaid = fields.Float(string='Saldo Awal Piutang')
    payment_progress = fields.Float(string='Pembayaran')
    invoice_unpaid = fields.Float(string='Saldo Akhir Piutang')
    total_quantity = fields.Float(string='Total Quantity')
    discount = fields.Float(string='Potongan Ambil Sendiri')
    net_sales = fields.Float(string='Net Sales')
    qty_delivered = fields.Float(string='Qty Dikirim')
    qty_tip = fields.Float(string='Qty Ambil sendiri')
    company_id = fields.Many2one('res.company', related='partner_id.company_id',string='Company')

    def get_main_request(self):
        request = """
            CREATE or REPLACE VIEW %s AS
                SELECT sr.partner_id AS partner_id,
                    to_char(sr.date,'YYYY') AS YEAR,
                    to_char(sr.date,'Month') AS MONTH,
                    ROW_NUMBER() OVER (ORDER BY sr.partner_id desc) AS id,
                    ppr.user_id,
                    user_partner.ref,
                    partner.code AS partner_code,
                    partner.name AS partner_name,
                    partner.region_master_id AS region_master_id,
                    ppr.customer_group AS customer_group_id,
					invoice_90.amount_total_signed as invoice_90,
                    invoice.amount_total_signed as payment,
                    invoice_last.amount_total_signed as payment_unpaid,
                    invoice_progress.amount_total_signed as payment_progress,
					invoice_unpaid.amount_total_signed as invoice_unpaid,
					invoice.quantity as total_quantity,
					sale_line.discount_fixed_line as discount,
					invoice.amount_total_signed / invoice.quantity as net_sales,
					take_in_plant.qty_invoiced as qty_tip,
					delivery.qty_invoiced as qty_delivered
                FROM sale_report sr
                JOIN res_partner partner ON partner.id = sr.partner_id
                JOIN partner_pricelist ppr ON ppr.partner_id = partner.id
                JOIN res_users ru ON ru.id = ppr.user_id
                JOIN res_partner user_partner ON user_partner.id = ru.partner_id
				LEFT JOIN (
                        SELECT partner_id,to_char(date,'Month') AS month_invoice,to_char(date,'YYYY') AS year_invoice,sum(abs(amount_total_signed)) as amount_total_signed
                        FROM account_move
                        WHERE state = 'posted' and type = 'out_invoice'
                        GROUP BY month_invoice,year_invoice,partner_id
                    ) AS invoice_90
                        ON sr.partner_id = invoice_90.partner_id AND invoice_90.month_invoice = to_char(sr.date::timestamp - '3 month'::interval,'Month') AND invoice_90.year_invoice = to_char(sr.date,'YYYY')
                LEFT JOIN (
                        SELECT am.partner_id,to_char(am.date,'Month') AS month_invoice,to_char(am.date,'YYYY') AS year_invoice,sum(abs(am.amount_total_signed)) as amount_total_signed, sum(aml.quantity) as quantity
                        FROM account_move am
						JOIN account_move_line aml ON aml.move_id = am.id
                        WHERE am.state = 'posted' and am.type='out_invoice' AND am.invoice_payment_state = 'paid' AND aml.exclude_from_invoice_tab = False
                        GROUP BY month_invoice,year_invoice,am.partner_id
                    ) AS invoice 
                        ON sr.partner_id = invoice.partner_id AND invoice.month_invoice = to_char(sr.date,'Month') AND invoice.year_invoice = to_char(sr.date,'YYYY')
                LEFT JOIN (
                        SELECT partner_id,to_char(date,'Month') AS month_invoice,to_char(date,'YYYY') AS year_invoice,sum(abs(amount_total_signed)) as amount_total_signed
                        FROM account_move
                        WHERE state = 'posted' and type = 'out_invoice' AND invoice_payment_state = 'not_paid'
                        GROUP BY month_invoice,year_invoice,partner_id
                    ) AS invoice_last
                        ON sr.partner_id = invoice_last.partner_id AND invoice_last.month_invoice = to_char(sr.date::timestamp - '1 month'::interval,'Month') AND invoice_last.year_invoice = to_char(sr.date,'YYYY')
                LEFT JOIN (
                        SELECT partner_id,to_char(date,'Month') AS month_invoice,to_char(date,'YYYY') AS year_invoice,sum(abs(amount_total_signed)) as amount_total_signed
                        FROM account_move
                        WHERE state = 'posted' and type = 'out_invoice' AND invoice_payment_state = 'in_payment'
                        GROUP BY month_invoice,year_invoice,partner_id
                    ) AS invoice_progress
                        ON sr.partner_id = invoice_progress.partner_id AND invoice_progress.month_invoice = to_char(sr.date::timestamp - '1 month'::interval,'Month') AND invoice_progress.year_invoice = to_char(sr.date,'YYYY')
                LEFT JOIN (
                        SELECT partner_id,to_char(date,'Month') AS month_invoice,to_char(date,'YYYY') AS year_invoice,sum(abs(amount_total_signed)) as amount_total_signed
                        FROM account_move
                        WHERE state = 'posted' and type = 'out_invoice' AND invoice_payment_state = 'not_paid'
                        GROUP BY month_invoice,year_invoice,partner_id
                    ) AS invoice_unpaid
                        ON sr.partner_id = invoice_unpaid.partner_id AND invoice_unpaid.month_invoice = to_char(sr.date,'Month') AND invoice_unpaid.year_invoice = to_char(sr.date,'YYYY')
                LEFT JOIN (
						SELECT so.partner_id,to_char(so.date_order,'Month') AS month_invoice,to_char(so.date_order,'YYYY') AS year_invoice,sum(sol.discount_fixed_line) as discount_fixed_line, sum(qty_invoiced) as qty_invoiced
						FROM sale_order so
						JOIN sale_order_line sol ON sol.order_id = so.id
						GROUP BY month_invoice,year_invoice,so.partner_id
					)AS sale_line
                        ON sr.partner_id = sale_line.partner_id AND sale_line.month_invoice = to_char(sr.date,'Month') AND sale_line.year_invoice = to_char(sr.date,'YYYY')
				LEFT JOIN (
						SELECT so.partner_id,to_char(so.date_order,'Month') AS month_invoice,to_char(so.date_order,'YYYY') AS year_invoice,sum(so_line.qty_invoiced) as qty_invoiced
						FROM sale_order so 
						LEFT JOIN  sale_order_line so_line ON so_line.order_id = so.id
						WHERE so.state = 'done' AND so.order_pickup_method_id = 2 AND so_line.is_reward_line = False
						GROUP BY month_invoice,year_invoice,so.partner_id
						) AS take_in_plant
							 ON sr.partner_id = take_in_plant.partner_id AND take_in_plant.month_invoice = to_char(sr.date,'Month') AND take_in_plant.year_invoice = to_char(sr.date,'YYYY')
				LEFT JOIN (
						SELECT so.partner_id,to_char(so.date_order,'Month') AS month_invoice,to_char(so.date_order,'YYYY') AS year_invoice,sum(so_line.qty_invoiced) as qty_invoiced
						FROM sale_order so 
						LEFT JOIN  sale_order_line so_line ON so_line.order_id = so.id
						WHERE so.state = 'done' AND so.order_pickup_method_id = 1 AND so_line.is_reward_line = False
						GROUP BY month_invoice,year_invoice,so.partner_id
						) AS delivery
							 ON sr.partner_id = delivery.partner_id AND delivery.month_invoice = to_char(sr.date,'Month') AND delivery.year_invoice = to_char(sr.date,'YYYY')
				GROUP BY sr.partner_id,
                        YEAR,
                        MONTH,
                        ppr.user_id,
                        user_partner.ref,
                        partner.code,
                        partner.name,
                        partner.region_master_id,
                        ppr.customer_group,
						invoice.amount_total_signed,
						invoice_90.amount_total_signed,
						invoice_last.amount_total_signed,
						invoice_progress.amount_total_signed,
						invoice_unpaid.amount_total_signed,
						invoice.quantity,
						sale_line.discount_fixed_line,
						take_in_plant.qty_invoiced,
						delivery.qty_invoiced
				ORDER BY YEAR, MONTH ASC;
                """ % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        # start_date = ''
        # end_date = ''
        # if self._context.get('start_date') and self._context.get('end_date'):
        #     start_date = self._context.get('start_date')
        #     end_date = self._context.get('end_date')
        # else:
        #     start_date = datetime.now().date()
        #     end_date = datetime.now().date()
        self.env.cr.execute(self.get_main_request())