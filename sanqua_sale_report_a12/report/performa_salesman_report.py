from odoo import api, fields, models, tools
import logging
from datetime import datetime
_logger = logging.getLogger(__name__)


class PerformaSalesmanReport(models.Model):
    _name = "report.performa.salesman"
    _description = "Performa Salesman Report"
    _auto = False
    _order = "id"
    
    user_id = fields.Many2one('res.users', string='Salesman')
    company_id = fields.Many2one('res.company', related='user_id.company_id',string='Company')
    product_id = fields.Many2one('product.product',string='Product')
    qty_realisasi = fields.Float(string='Realisasi')
    qty_target = fields.Float(string='Target')
    persentase = fields.Float(string='Persentase (%)')
    biaya = fields.Float(string='Biaya')

    def get_main_request(self, bulan, tahun):
        # request = """
        #     CREATE or REPLACE VIEW %s AS
        #         SELECT 
        #             ROW_NUMBER() OVER (ORDER BY sr.product_id desc) AS id,
        #             prod.default_code as product_code,
        #             sr.product_id,
        #             sr.user_id,
        #             sum(sr.qty_delivered) as qty_realisasi,
        #             (SELECT sum(tl.qty) from sales_user_target_line tl where tl.user_id = sr.user_id and
        #             tl.month = '%s' AND tl.year = '%s' AND tl.product_id = sr.product_id
        #             group by tl.user_id) as qty_target,
        #             sum(sr.qty_delivered) / (SELECT sum(tl.qty) from sales_user_target_line tl where tl.user_id = sr.user_id and
        #             tl.month = '%s' AND tl.year = '%s' AND tl.product_id = sr.product_id
        #             group by tl.user_id) * 100  as persentase
        #         FROM sale_report sr
        #         LEFT JOIN product_product prod ON prod.id = sr.product_id
                
        #         WHERE EXTRACT(MONTH from sr.date) = %s AND EXTRACT(YEAR from sr.date) = %s
        #         GROUP BY 
        #             prod.default_code,
        #             sr.product_id,
        #             sr.user_id;
        #         """ % (self._table, bulan, tahun, bulan, tahun, bulan, tahun)
        request = """
            CREATE or REPLACE VIEW %s AS
            select
                concat(tl.user_id, tl.product_id) as id,
                tl.product_id,
                tl.user_id,
                sum(tl.qty) as qty_target,
                (SELECT sum(sr.qty_delivered) FROM sale_report sr 
                    WHERE sr.user_id = tl.user_id AND
                            EXTRACT(MONTH from sr.date) = %s AND EXTRACT(YEAR from sr.date) = %s
                            AND sr.product_id = tl.product_id) as qty_realisasi,
                (SELECT sum(sr.qty_delivered) FROM sale_report sr 
                    WHERE sr.user_id = tl.user_id AND
                            EXTRACT(MONTH from sr.date) = %s AND EXTRACT(YEAR from sr.date) = %s
                            AND sr.product_id = tl.product_id) / sum(tl.qty) * 100 as persentase,
                (SELECT ABS(sum(aml.balance)) from account_move_line aml 
                LEFT JOIN account_account aa ON aa.id = aml.account_id
                WHERE aml.partner_id = tl.user_id AND aa.user_type_id = 15 AND
                    EXTRACT(MONTH from aml.date) = %s AND EXTRACT(YEAR from aml.date) = %s) as biaya
                FROM sales_user_target_line tl
                WHERE tl.month = '%s' AND tl.year = '%s'
                GROUP BY tl.user_id, tl.product_id, concat(tl.user_id, tl.product_id);
                """ % (self._table, bulan, tahun, bulan, tahun, bulan, tahun, bulan, tahun)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        bulan = 1
        tahun = 2021
        if self._context.get('bulan') and self._context.get('tahun'):
            bulan = self._context.get('bulan')
            tahun = self._context.get('tahun')
        self.env.cr.execute(self.get_main_request(bulan, tahun))