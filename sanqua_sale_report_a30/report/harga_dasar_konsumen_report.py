from odoo import api, fields, models, tools
import logging
_logger = logging.getLogger(__name__)


class HargaDasarKonsumenReport(models.Model):
    _name = "report.harga.dasar.konsumen"
    _description = "Harga dasar konsumen Report"
    _auto = False
    _order = "id ASC"

    partner_id = fields.Many2one('res.partner', string='Partner ID')
    partner_code = fields.Char(string='Outlet Code')
    partner_name = fields.Char(string='Outlet Name')
    region_master_id = fields.Many2one('region.master', related='partner_id.region_master_id' ,string='Area')
    region_group_id = fields.Many2one('region.group', related='partner_id.region_group_id' ,string='Group')
    user_id = fields.Many2one('res.users', string='Salesperson')
    team_id = fields.Many2one('crm.team', string='Division')
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist')
    product_pricelis_id = fields.Many2one('product.pricelist.item', string='Product')
    fixed_price = fields.Float(string='Price')
    company_id = fields.Many2one('res.company', string='Company')

    def get_main_request(self):
        request = """
            CREATE or REPLACE VIEW %s AS
                SELECT 
                    CONCAT(lpad(pp.partner_id::TEXT, 5,'0'),rpad(pp.user_id::TEXT,4,'0'),rpad(pp.team_id::TEXT,3,'0'),rpad(ppi.id::TEXT,5,'0'))::BIGINT as id,
                    pp.partner_id,
                    partner.code AS partner_code,
                    partner.name AS partner_name,
                    pp.user_id, 
                    pp.team_id,
                    pp.pricelist_id as pricelist_id, 
                    ppi.id as product_pricelis_id,
                    ppi.fixed_price as fixed_price,
                    pp.company_id
                FROM partner_pricelist pp
                LEFT JOIN product_pricelist_item ppi ON ppi.pricelist_id = pp.pricelist_id
                LEFT JOIN product_product ppx ON ppx.id = ppi.product_id
                LEFT JOIN product_template pt ON ppx.product_tmpl_id = pt.id
                LEFT JOIN crm_team ct ON ct.id = pp.team_id
                LEFT JOIN res_partner partner ON partner.id = pp.partner_id
                WHERE ct.state = 'done' and ct.name in ('SQA','BTV','BVG','GLN') AND pt.product_classification = 'barangjadi'
                ORDER BY pp.id;
                """ % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())