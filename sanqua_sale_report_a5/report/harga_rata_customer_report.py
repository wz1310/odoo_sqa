from odoo import api, fields, models, tools
import logging
_logger = logging.getLogger(__name__)


class HargaRataCustomerReport(models.Model):
    _name = "report.harga.rata.customer"
    _description = "Harga Rata-rata Customer Report"
    _auto = False
    _order = "id ASC"

    partner_id = fields.Many2one('res.partner', string='Partner ID')
    sale_id = fields.Many2one('sale.order', string='Sale')
    order_date = fields.Date(string='Date')
    partner_code = fields.Char(string='Outlet Code')
    partner_name = fields.Char(string='Outlet Name')
    customer_group_id = fields.Many2one('customer.group',string='Class Outlet')
    order_pickup_method_id = fields.Many2one('order.pickup.method', string='AS / K')
    ref_product = fields.Char(string="Product Code")
    product_id = fields.Many2one('product.product', string='Product ID')
    product_name = fields.Char(string='Product')
    qty = fields.Float(string='Quantity')
    price_total = fields.Monetary(string='Price Total')
    currency_id = fields.Many2one('res.currency', string='Currency')
    discount_amount = fields.Float(string='Discount')
    harga_rata = fields.Float(string='Average Cost')
    potongan_as = fields.Float(string='Discount AS')
    potongan_ba = fields.Float(string='Discount BA')
    potongan_diskon_target = fields.Float(string='Discount Target')
    harga_rata_bersih = fields.Float(string='Average')
    harga_ambil_sendiri = fields.Float(string='Disc. Take in Plant')
    harga_kirim = fields.Float(string='Delivery Amount')

    company_id = fields.Many2one('res.company', string='Company')

    def get_main_request(self):
        request = """
            CREATE or REPLACE VIEW %s AS
                SELECT 
                    ROW_NUMBER() OVER (ORDER BY sr.order_id desc) AS id,
                    sr.order_id  AS sale_id,
                    sr.date as order_date,
                    ppr.currency_id,
                    partner.code AS partner_code,
                    partner.name AS partner_name,
                    sr.partner_id AS partner_id,
                    p_list.customer_group AS customer_group_id,
                    so.order_pickup_method_id AS order_pickup_method_id,
                    pp.default_code as ref_product,
                    pt.name as product_name,
                    sr.product_id AS product_id,
                    sr.qty_delivered AS qty,
                    sr.price_total AS price_total,
                    sr.discount_amount AS discount_amount,
                    CASE WHEN
                        (sr.qty_delivered > 0) 
                    THEN (sr.price_total / sr.qty_delivered)
                    ELSE 0
                    END
                    AS harga_rata,
					CASE WHEN
						so.order_pickup_method_id = 2
					THEN disc_take_in_plant.disc_amount
					ELSE 0
					END AS potongan_as,
                    dtsc_support.discount_amount AS potongan_ba,
                    dtsc_target.discount_amount AS potongan_diskon_target,
                    CASE WHEN
                        (sr.qty_delivered > 0) 
                    THEN ((sr.price_total / sr.qty_delivered) - ((sr.price_total / sr.qty_delivered) + 0))
                    ELSE 0
                    END
                    AS harga_rata_bersih,
                    CASE WHEN
                        (sr.qty_delivered > 0) 
                    THEN sr.price_total - disc_take_in_plant.disc_amount / sr.qty_delivered
                    ELSE 0
                    END
                    AS harga_ambil_sendiri,
                    CASE WHEN
                        (sr.qty_delivered > 0) 
                    THEN (sr.price_total / sr.qty_delivered)
                    ELSE 0
                    END
                    AS harga_kirim,
                    so.company_id AS company_id
                FROM sale_report sr
                LEFT JOIN res_partner partner ON partner.id = sr.partner_id
                LEFT JOIN sale_order so ON so.id = sr.order_id
                LEFT JOIN partner_pricelist p_list ON p_list.id = so.partner_pricelist_team_id
                LEFT JOIN product_product pp ON sr.product_id = pp.id
                LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                LEFT JOIN product_pricelist ppr ON ppr.id = so.pricelist_id
				LEFT JOIN (
					SELECT dtsc.partner_id, dtsc_line.product_id,dtsc.realization_date_start,dtsc.realization_date_end, sum(dtsc_line.discount_amount) as discount_amount  
					FROM discount_target_support_customer dtsc
					LEFT JOIN discount_target_support_customer_line dtsc_line ON dtsc_line.discount_id = dtsc.id
					LEFT JOIN discount_target_support_master dtsm ON dtsc.master_id = dtsm.id
					WHERE dtsm.disc_type='target'
					GROUP BY dtsc.partner_id, dtsc_line.product_id,dtsc.realization_date_start,dtsc.realization_date_end) AS dtsc_target ON dtsc_target.partner_id = sr.partner_id AND sr.date::DATE BETWEEN dtsc_target.realization_date_start AND dtsc_target.realization_date_end
				LEFT JOIN (
					SELECT dtsc.partner_id, dtsc_line.product_id,dtsc.realization_date_start,dtsc.realization_date_end, sum(dtsc_line.discount_amount) as discount_amount  
					FROM discount_target_support_customer dtsc
					LEFT JOIN discount_target_support_customer_line dtsc_line ON dtsc_line.discount_id = dtsc.id
					LEFT JOIN discount_target_support_master dtsm ON dtsc.master_id = dtsm.id
					WHERE dtsm.disc_type='support'
					GROUP BY dtsc.partner_id, dtsc_line.product_id,dtsc.realization_date_start,dtsc.realization_date_end) AS dtsc_support ON dtsc_support.partner_id = sr.partner_id AND sr.date::DATE BETWEEN dtsc_support.realization_date_start AND dtsc_support.realization_date_end
				LEFT JOIN (
					SELECT rd.region_group_id, rd.team_id, rdp.product_id, rdp.disc_amount FROM region_discount rd
					LEFT JOIN region_discount_product rdp ON rdp.region_discount_id = rd.id
				) AS disc_take_in_plant ON disc_take_in_plant.region_group_id = partner.region_group_id AND disc_take_in_plant.team_id = sr.team_id AND disc_take_in_plant.product_id = sr.product_id
                """ % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())