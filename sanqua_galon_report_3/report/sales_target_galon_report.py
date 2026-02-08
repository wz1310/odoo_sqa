from odoo import api, fields, models, tools
import logging
_logger = logging.getLogger(__name__)

from datetime import datetime

class SalesTargetGalonReport(models.Model):
    _name = "report.sales.target.galon"
    _description = "Sales Target Galon Report"
    _auto = False
    _order = "id DESC"

    user_id = fields.Many2one('res.users', string='Salesman')
    team_id = fields.Many2one('crm.team', string='Divisi')
    partner_code = fields.Char('Partner Code')
    partner_name = fields.Char('Partner Name')
    partner_id = fields.Many2one('res.partner', string='Partner')
    region_master_id = fields.Many2one('region.master', string='Area')
    region_id = fields.Many2one('region.region', string='Grouping')
    product_id = fields.Many2one('product.product', string='Product')
    jan = fields.Float(string='Januari')
    feb = fields.Float(string='Februari')
    mar = fields.Float(string='Maret')
    apr = fields.Float(string='April')
    mei = fields.Float(string='Mei')
    jun = fields.Float(string='Juni')
    jul = fields.Float(string='Juli')
    ags = fields.Float(string='Agustus')
    sept = fields.Float(string='September')
    okt = fields.Float(string='Oktober')
    nov = fields.Float(string='November')
    des = fields.Float(string='Desember')
    total = fields.Float(string='Total')
    company_id = fields.Many2one('res.company', string='Company')


    def get_main_request(self,year):
        request = """
            CREATE or REPLACE VIEW %s AS
                SELECT 
                    CONCAT(lpad(main.user_id::TEXT, 5,'0'),rpad(main.team_id::TEXT,3,'0'),rpad(main.partner_id::TEXT,5,'0'),rpad(main.region_master_id::TEXT,2,'0'),rpad(main.product_id::TEXT,5,'0'))::BIGINT as id,
                    main.user_id,
                    main.team_id,
                    main.partner_id,
                    main.code as partner_code,
                    main.name as partner_name,
                    main.region_master_id,
                    main.region_id,
                    main.product_id,
                    sum(main.qty) filter(WHERE main.month = '1' and main.year = '%s') as jan,
                    sum(main.qty) filter(WHERE main.month = '2' and main.year = '%s') as feb,
                    sum(main.qty) filter(WHERE main.month = '3' and main.year = '%s') as mar,
                    sum(main.qty) filter(WHERE main.month = '4' and main.year = '%s') as apr,
                    sum(main.qty) filter(WHERE main.month = '5' and main.year = '%s') as mei,
                    sum(main.qty) filter(WHERE main.month = '6' and main.year = '%s') as jun,
                    sum(main.qty) filter(WHERE main.month = '7' and main.year = '%s') as jul,
                    sum(main.qty) filter(WHERE main.month = '8' and main.year = '%s') as ags,
                    sum(main.qty) filter(WHERE main.month = '9' and main.year = '%s') as sept,
                    sum(main.qty) filter(WHERE main.month = '10' and main.year = '%s') as okt,
                    sum(main.qty) filter(WHERE main.month = '11' and main.year = '%s') as nov,
                    sum(main.qty) filter(WHERE main.month = '12' and main.year = '%s') as des,
                    sum(main.qty) filter(WHERE main.year = '%s') as total,
                    main.company_id
                FROM	(SELECT 
                            sut.user_id,
                            sut.team_id,
                            sut.year,
                            sut.month,
                            sut_line.partner_id,
                            rp.name,
                            rp.code,
                            sut_line.region_master_id,
                            sut_line.region_id,
                            sut_line.product_id,
                            sut_line.qty,
                            sut.company_id
                        FROM sales_user_target sut
                        JOIN sales_user_target_line sut_line ON sut.id = sut_line.target_id
                        left join res_partner rp on sut_line.partner_id = rp.id
                        WHERE sut.state = 'done') as main
                GROUP BY
                    main.user_id,
                    main.team_id,
                    main.partner_id,
                    main.code,
                    main.name,
                    main.region_master_id,
                    main.region_id,
                    main.product_id,
                    main.company_id;
                """ % (self._table, year, year, year, year, year, year, year
                , year, year, year, year, year, year)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        year = ''
        if self._context.get('year'):
            year = self._context.get('year')
        else:
            year = str(datetime.now().date().strftime('%Y'))
        self.env.cr.execute(self.get_main_request(year))
