from odoo import api, fields, models, tools
import logging
from datetime import datetime
_logger = logging.getLogger(__name__)


class AnnualSalesTargetReport(models.Model):
    _name = "report.annual.sales.target"
    _description = "Annual Sales Target Report"
    _auto = False
    _order = "id"

    ref = fields.Char(string='Sales ID')
    user_id = fields.Many2one('res.users', string='Salesman')
    partner_code = fields.Char(string='Customer Code')
    partner_id = fields.Many2one('res.partner', string='Customer')
    region_id = fields.Many2one('region.region', string='Area')
    region_group_id = fields.Many2one('region.group', string='Region Group')
    product_code = fields.Char(string='Product Code')
    product_id = fields.Many2one('product.product', string='Product Name')
    januari = fields.Float(string='Januari')
    februari = fields.Float(string='Februari')
    maret = fields.Float(string='Maret')
    april = fields.Float(string='April')
    mei = fields.Float(string='Mei')
    juni = fields.Float(string='Juni')
    juli = fields.Float(string='Juli')
    agustus = fields.Float(string='Agustus')
    september = fields.Float(string='September')
    oktober = fields.Float(string='Oktober')
    november = fields.Float(string='November')
    desember = fields.Float(string='Desember')
    company_id = fields.Many2one('res.company', related='user_id.company_id',string='Company')
    
    

    def get_main_request(self,years):
        request = """
            CREATE or REPLACE VIEW %s AS
                SELECT 
                    ROW_NUMBER() OVER (ORDER BY sr.partner_id desc) AS id,
                    user_partner.ref as ref,
                    ppr.user_id,
                    partner.code AS partner_code,
                    sr.partner_id AS partner_id,
                    partner.region_id AS region_id,
                    partner.region_group_id AS region_group_id,
                    ppr.customer_group AS customer_group_id,
                    prod.default_code as product_code,
                    sr.product_id,
                    sum(sales_target.januari) as januari,
                    sum(sales_target.februari) as februari,
                    sum(sales_target.maret) as maret,
                    sum(sales_target.april) as april,
                    sum(sales_target.mei) as mei,
                    sum(sales_target.juni) as juni,
                    sum(sales_target.juli) as juli,
                    sum(sales_target.agustus) as agustus,
                    sum(sales_target.september) as september,
                    sum(sales_target.oktober) as oktober,
                    sum(sales_target.november) as november,
                    sum(sales_target.desember) as desember
                FROM sale_report sr
                LEFT JOIN res_partner partner ON partner.id = sr.partner_id
                LEFT JOIN partner_pricelist ppr ON ppr.partner_id = partner.id
                LEFT JOIN res_users ru ON ru.id = ppr.user_id
                LEFT JOIN res_partner user_partner ON user_partner.id = ru.partner_id
                LEFT JOIN product_product prod ON prod.id = sr.product_id
                JOIN (
                    SELECT 
                            sut.id,
                            sut.user_id,
                            sut_line.product_id,
                            sut_line.partner_id,
                            sut_line.customer_group_id,
                            (CASE WHEN sut.year = '%s' AND LPAD(sut.month,2,'0') = '01' THEN sut_line.qty ELSE 0 END) AS januari,
                            (CASE WHEN sut.year = '%s' AND LPAD(sut.month,2,'0') = '02' THEN sut_line.qty ELSE 0 END) AS februari,
                            (CASE WHEN sut.year = '%s' AND LPAD(sut.month,2,'0') = '03' THEN sut_line.qty ELSE 0 END) AS maret,
                            (CASE WHEN sut.year = '%s' AND LPAD(sut.month,2,'0') = '04' THEN sut_line.qty ELSE 0 END) AS april,
                            (CASE WHEN sut.year = '%s' AND LPAD(sut.month,2,'0') = '05' THEN sut_line.qty ELSE 0 END) AS mei,
                            (CASE WHEN sut.year = '%s' AND LPAD(sut.month,2,'0') = '06' THEN sut_line.qty ELSE 0 END) AS juni,
                            (CASE WHEN sut.year = '%s' AND LPAD(sut.month,2,'0') = '07' THEN sut_line.qty ELSE 0 END) AS juli,
                            (CASE WHEN sut.year = '%s' AND LPAD(sut.month,2,'0') = '08' THEN sut_line.qty ELSE 0 END) AS agustus,
                            (CASE WHEN sut.year = '%s' AND LPAD(sut.month,2,'0') = '09' THEN sut_line.qty ELSE 0 END) AS september,
                            (CASE WHEN sut.year = '%s' AND LPAD(sut.month,2,'0') = '10' THEN sut_line.qty ELSE 0 END) AS oktober,
                            (CASE WHEN sut.year = '%s' AND LPAD(sut.month,2,'0') = '11' THEN sut_line.qty ELSE 0 END) AS november,
                            (CASE WHEN sut.year = '%s' AND LPAD(sut.month,2,'0') = '12' THEN sut_line.qty ELSE 0 END) AS desember,
                            sut.company_id
                    FROM sales_user_target sut
                    JOIN sales_user_target_line sut_line ON sut_line.target_id=sut.id
                    WHERE sut_line.target_id=sut.id AND sut.state = 'done'
                    ) AS sales_target  
                        ON  sales_target.user_id = sr.user_id
                        AND sales_target.partner_id = sr.partner_id
                        AND sales_target.product_id = sr.product_id
                        AND sales_target.customer_group_id = ppr.customer_group
                GROUP BY
                    user_partner.ref,
                    ppr.user_id,
                    partner.code,
                    sr.partner_id,
                    partner.region_id,
                    partner.region_group_id,
                    ppr.customer_group,
                    prod.default_code,
                    sr.product_id;
                """ % (self._table,years,years,years,years,years,years,years,years,years,years,years,years)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        year = ''
        if self._context.get('year'):
            year = self._context.get('year')
        else:
            year = str(datetime.now().date().strftime('%Y'))
        self.env.cr.execute(self.get_main_request(year))