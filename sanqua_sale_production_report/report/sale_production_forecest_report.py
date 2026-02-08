from odoo import api, fields, models, tools
import logging
_logger = logging.getLogger(__name__)


class SaleProductionForecastReport(models.Model):
	_name = "report.sale.production.forecast"
	_description = "Sale Production Forecast Report"
	_auto = False
	_order = "product_id ASC"

	date = fields.Date(string='Date')
	product_id = fields.Many2one('product.product', string='Product')
	qty_order = fields.Float(string='Qty Order')
	qty_production = fields.Float(string='Qty Production')
	qty_forecast = fields.Float(string='Qty Forecast')
	company_id = fields.Many2one('res.company', string='Company')

	def get_main_request(self):
		request = """
			CREATE or REPLACE VIEW %s AS
				SELECT 
					sr.product_id AS id,
					DATE(sr.date) AS date, 
					sr.product_id,
					sum(sr.product_uom_qty) AS qty_order, 
					sum(mp.product_qty) AS qty_production,
					sum(mp.product_qty) AS qty_forecast,
					sr.company_id
				FROM sale_report sr
				LEFT JOIN mrp_production mp ON sr.product_id = mp.product_id
				WHERE mp.state = 'done'
				GROUP BY DATE(sr.date), sr.product_id,sr.company_id;
				""" % (self._table)
		return request

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute(self.get_main_request())