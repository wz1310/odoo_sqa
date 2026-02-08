from odoo import api, fields, models, tools
import logging
from datetime import datetime
_logger = logging.getLogger(__name__)


class GlobalDivisionSummarySalesReport(models.Model):
    _name = "report.global.division.summary.sales.21"
    _description = "Global Division Summary Sales Report"
    _auto = False
    _order = "id"
    
    team_id = fields.Many2one('crm.team',string='Sales Team')
    team_name = fields.Char(related='team_id.name',string='Sales Team Name')
    sut_line = fields.Many2one('sales.user.target.line', string='SUT LINE')
    # product_id = fields.Many2one('product.product', string='Product')
    date = fields.Date(string='Date')
    qty_realisasi = fields.Float(string='Realisasi')
    qty_target = fields.Float(string='Target')
    accumulate = fields.Float(string='Accumulate')
    persentase = fields.Float(string='Persentase (%)')
    company_id = fields.Many2one('res.company',string='Company')

    def get_main_request(self):
        request = """
            CREATE or REPLACE VIEW %s AS
            SELECT 
                sr.team_id as id,
                sr.team_id,
                sr.date::DATE as date,
                coalesce(sum(sr.qty_delivered), 0) as qty_realisasi,
                (SELECT sum(tl.target_per_day) from sales_user_target_line tl
                    WHERE tl.year = EXTRACT(YEAR from sr.order_date)::TEXT AND tl.month = EXTRACT(MONTH from sr.order_date)::TEXT
                    AND tl.team_id = sr.team_id
                    group by tl.team_id) as qty_target,
                coalesce((sum(sr.qty_delivered) - (SELECT sum(tl.target_per_day) from sales_user_target_line tl
                    WHERE tl.year = EXTRACT(YEAR from sr.order_date)::TEXT AND tl.month = EXTRACT(MONTH from sr.order_date)::TEXT
                    AND tl.team_id = sr.team_id
                    group by tl.team_id) ), 0) as accumulate,
                coalesce((sum(sr.qty_delivered)/ (SELECT sum(tl.target_per_day) from sales_user_target_line tl
                    WHERE tl.year = EXTRACT(YEAR from sr.order_date)::TEXT AND tl.month = EXTRACT(MONTH from sr.order_date)::TEXT
                    AND tl.team_id = sr.team_id
                    group by tl.team_id)), 0) * 100 as persentase,
                sr.company_id
            FROM sale_report sr
			GROUP BY sr.team_id,sr.date::DATE,sr.order_date,sr.company_id
                """ % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())