from odoo import api, fields, models, tools
import logging
_logger = logging.getLogger(__name__)


class M4Report(models.Model):
    _name = "report.m4"
    _description = "M4 Report"
    _auto = False
    _order = "id DESC"

    code = fields.Char('Code')
    partner_name = fields.Char('Partner Name')
    partner_id = fields.Many2one('res.partner', string='Partner')
    category_id = fields.Many2many('res.partner.category', related='partner_id.category_id', string='Kategori Piutang')
    pricelist_id = fields.Many2one('partner.pricelist', string='Pricelist')
    customer_group = fields.Many2one('customer.group',string='Katagori')
    team_id = fields.Many2one('crm.team', string='Divisi')
    user_id = fields.Many2one('res.users', string='Salesman')
    credit_limit = fields.Float(string='Limit')
    remaining_limit = fields.Float(string='Sisa Limit',compute='get_remaining_limit')
    payment_term_id = fields.Many2one('account.payment.term', string='TOP')
    region_master_id = fields.Many2one('region.master', string='Area')
    company_id = fields.Many2one('res.company', string='Company')
    target_qty = fields.Float(string='Target QTY')
    omzet_qty = fields.Float(string='Omzet QTY')
    omzet_amount = fields.Float(string='Omzet Amount')
    pencapaian = fields.Float(string='Pencapaian (%)')
    payment = fields.Float(string='Pembayaran')
    overlimit_status = fields.Char(compute='_compute_overlimit_status', string='OL/NO OL')

    @api.depends('credit_limit','omzet_amount')
    def get_remaining_limit(self):
        for rec in self:
            rec.remaining_limit = rec.credit_limit - rec.omzet_amount
    

    @api.depends('pricelist_id')
    def _compute_overlimit_status(self):
        for rec in self:
            res = 'NO OL'
            if rec.omzet_amount > rec.pricelist_id.credit_limit:
                res = 'OL'
            rec.overlimit_status = res


    def get_main_request(self):
        request = """
            CREATE or REPLACE VIEW %s AS
                SELECT             
                    CONCAT(lpad(rp.id::TEXT, 5,'0'),rpad(pp.customer_group::TEXT,3,'0'),rpad(pp.user_id::TEXT,4,'0'),rpad(rp.region_master_id::TEXT,2,'0'),rpad(pp.payment_term_id::TEXT,2,'0'))::BIGINT as id,
                    rp.id as partner_id, 
					pp.id as pricelist_id,
                    pp.customer_group,
                    pp.team_id ,
                    pp.user_id,
                    pp.credit_limit,
                    rp.region_master_id,
                    pp.company_id,
                    pp.payment_term_id,
					sum(COALESCE(sut_line.qty,0)) as target_qty,
					sum(aml.quantity) as omzet_qty,
					sum(aml.price_subtotal) as omzet_amount,
					CASE WHEN sum(COALESCE(sut_line.qty,0)) > 0 THEN sum(aml.quantity) / sum(COALESCE(sut_line.qty,0)) ELSE 0 END as pencapaian,
					sum(ap.amount) as payment,
                    rp.code,
                    rp.name as partner_name
                FROM partner_pricelist pp
				JOIN res_partner rp ON pp.partner_id = rp.id 
				JOIN crm_team ct ON pp.team_id = ct.id
				LEFT JOIN account_move am ON am.partner_id = pp.partner_id and am.invoice_user_id = pp.user_id and am.invoice_payment_term_id = pp.payment_term_id and am.company_id = pp.company_id and am.team_id = pp.team_id and am.state in ('posted')
				LEFT JOIN account_move_line aml ON aml.move_id = am.id and aml.exclude_from_invoice_tab = False
				JOIN product_product p_p ON p_p.id = aml.product_id
				JOIN product_template pt ON pt.id = p_p.product_tmpl_id
				JOIN product_category pc ON pc.id = pt.categ_id and pc.report_category = 'gln'
				LEFT JOIN sales_user_target sut ON sut.team_id = pp.team_id and sut.user_id = pp.user_id and sut.company_id = pp.company_id 
				LEFT JOIN sales_user_target_line sut_line ON sut_line.target_id = sut.id and sut_line.partner_id = pp.partner_id and sut_line.customer_group_id = pp.customer_group and sut_line.product_id = aml.product_id
				LEFT JOIN account_payment ap ON ap.partner_id = pp.partner_id and ap.payment_type = 'inbound'
				WHERE ct.name = 'GLN'
				GROUP BY rp.id, 
					pp.id,
                    pp.customer_group,
                    pp.team_id ,
                    pp.user_id,
                    pp.credit_limit,
                    rp.region_master_id,
                    pp.company_id,
                    pp.payment_term_id;
                """ % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())
