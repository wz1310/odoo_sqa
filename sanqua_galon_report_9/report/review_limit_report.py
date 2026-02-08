from odoo import api, fields, models, tools
import logging
_logger = logging.getLogger(__name__)


class ReviewLimitReport(models.Model):
    _name = "report.review.limit"
    _description = "Review Limit Report"
    _auto = False
    _order = "id DESC"

    partner_code = fields.Char('Partner Code')
    partner_name = fields.Char('Partner Name')
    pricelist_id = fields.Many2one('partner.pricelist', string='Pricelist')
    partner_id = fields.Many2one('res.partner', string='Partner')
    payment_term_id = fields.Many2one('account.payment.term', string='Term of Payments')
    credit_limit = fields.Float(string='Credit Limit')
    omzet_amount = fields.Float(string='Omzet')
    piutang = fields.Float(related='pricelist_id.current_credit',string='Piutang')
    company_id = fields.Many2one('res.company', string='Company')


    def get_main_request(self):
        request = """
            CREATE or REPLACE VIEW %s AS
                SELECT pp.id,pp.id as pricelist_id,pp.partner_id, pp.payment_term_id, pp.credit_limit, sum(aml.price_subtotal) as omzet_amount, pp.company_id, rp.name as partner_name, rp.code as partner_code
                FROM partner_pricelist pp
                JOIN crm_team ct ON ct.id = pp.team_id and ct.name = 'GLN'
                LEFT JOIN res_partner rp ON rp.id = pp.partner_id
                LEFT JOIN account_move am ON am.partner_id = pp.partner_id and am.invoice_user_id = pp.user_id and am.invoice_payment_term_id = pp.payment_term_id and am.company_id = pp.company_id and am.team_id = pp.team_id and am.state in ('posted')
                LEFT JOIN account_move_line aml ON aml.move_id = am.id and aml.exclude_from_invoice_tab = False
                JOIN product_product p_p ON p_p.id = aml.product_id
                JOIN product_template pt ON pt.id = p_p.product_tmpl_id
                JOIN product_category pc ON pc.id = pt.categ_id and pc.report_category = 'gln'
                GROUP BY pp.id,pp.partner_id, pp.payment_term_id, pp.credit_limit, rp.name, rp.code
                ORDER BY pp.id;
                """ % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())
