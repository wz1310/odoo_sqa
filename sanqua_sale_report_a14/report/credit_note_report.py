from odoo import api, fields, models, tools
import logging
_logger = logging.getLogger(__name__)


class ReportCreditNote(models.Model):
    _name = "report.credit.note"
    _description = "Credit Note Report"
    _auto = False
    _order = "cn_date DESC"

    partner_code = fields.Char(string='Kode Pelanggan')
    partner_id = fields.Many2one('res.partner', string='Nama Pelanggan')
    product_code = fields.Char('Kode Barang')
    product_name = fields.Char('Type')
    product_id = fields.Many2one('product.product', string='Nama Product')
    refund_qty = fields.Float('Qty')
    subtotal = fields.Float('Nominal')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    cn_date = fields.Date('Tanggal CN')
    cn_number = fields.Char('No. CN')
    cn_state = fields.Selection(selection=[
            ('draft', 'Draft'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled')
        ], string='CN Status')
    sj_number = fields.Char('No. Surat Jalan')
    sales_admin_id = fields.Many2one('res.users', string='Admin')
    customer_group_id = fields.Many2one('customer.group',string='Class Outlet')
    user_id = fields.Many2one('res.users', string='Salesman')
    region_group_id = fields.Many2one('region.group', string='Region Group')
    region_master_id = fields.Many2one('region.master', string='Area')
    region_id = fields.Many2one('region.region', string='Region')
    company_id = fields.Many2one('res.company', string='Company')
    division_id = fields.Many2one('crm.team', string='Division')

    def get_main_request(self):
        request = """
            CREATE or REPLACE VIEW %s AS
                SELECT
                    aml.id as id,
                    rp.code as partner_code,
                    rp.id as partner_id,
                    pp.default_code as product_code,
                    pt.name as product_name,
                    aml.product_id as product_id,
                    aml.quantity as refund_qty,
                    aml.price_subtotal as subtotal,
                    am.invoice_date as cn_date,
                    aml.move_id as invoice_id,
                    am.state as cn_state,
                    am.name as cn_number,
                    am.invoice_origin as sj_number,
                    am.company_id as company_id,
                    ppr.sales_admin_id as sales_admin_id,
                    ppr.customer_group AS customer_group_id,
                    ppr.user_id as user_id,
                    rp.region_group_id,
                    rp.region_master_id,
                    rp.region_id,
                    am.team_id as division_id
                FROM account_move_line aml 
                LEFT JOIN account_move am ON am.id = aml.move_id
                LEFT JOIN res_partner rp ON rp.id = am.partner_id
                LEFT JOIN product_product pp ON pp.id = aml.product_id
                LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                JOIN partner_pricelist ppr ON ppr.partner_id = rp.id and am.team_id = ppr.team_id
                WHERE am.type = 'out_refund' AND exclude_from_invoice_tab = False AND am.state = 'posted'
                """ % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())
