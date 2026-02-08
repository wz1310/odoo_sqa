from odoo import api, fields, models, tools
import logging
_logger = logging.getLogger(__name__)


class LimitCreditReport(models.Model):
    _name = "report.limit.credit"
    _description = "Limit Credit Report"
    _auto = False
    _order = "id DESC"

    sale_id = fields.Many2one('sale.order', string='Sale')
    partner_id = fields.Many2one('res.partner', string='Customer')
    partner_code = fields.Char(string='No. Customer')
    user_id = fields.Many2one('res.users', string='Sales')
    sales_admin_id = fields.Many2one('res.users', string='Admin')
    payment_term_id = fields.Many2one('account.payment.term', string='TOP')
    credit_limit_value = fields.Monetary(string='Limit')
    amount_total = fields.Monetary(string='SO')
    amount_surat_jalan = fields.Monetary(string='Surat Jalan')
    amount_residual = fields.Monetary(string='Invoice')
    total = fields.Monetary(string='TOTAL REALISASI LIMIT')
    spare = fields.Monetary(string='Spare')
    tags = fields.Text(string='Tags')
    company_id = fields.Many2one('res.company', string='Company')
    currency_id = fields.Many2one('res.currency', string='Currency')

    def get_main_request1(self):
        request = """
            CREATE or REPLACE VIEW %s AS
                SELECT 
                    main.*,
                     (COALESCE(main.amount_total,0) + COALESCE(main.amount_surat_jalan,0) + COALESCE(main.amount_residual,0)) AS total, 
                     (COALESCE(main.credit_limit_value,0) - (COALESCE(main.amount_total,0) + COALESCE(main.amount_surat_jalan,0) + COALESCE(main.amount_residual,0))) AS spare
                FROM 
				( SELECT
                    CONCAT(lpad(partner.id::TEXT, 5,'0'),rpad(p_list.sales_admin_id::TEXT,5,'0'))::BIGINT as id,
                    partner.id AS partner_id,
                    partner.code AS partner_code,
                    so.user_id AS user_id,
                    p_list.sales_admin_id AS sales_admin_id,
                    so.payment_term_id AS payment_term_id,
                    sum(so.credit_limit_value) AS credit_limit_value,
 				 	sum(so_draft.amount_total) AS amount_total,
 				 	sum(so_done.amount_total) AS amount_surat_jalan,
				 	( SELECT	
                        sum(mv.amount_residual)
					  FROM account_move mv
                      WHERE mv.partner_id = partner.id AND mv.invoice_user_id = so.user_id)
                       AS amount_residual,
					( SELECT name 
                      FROM 
                          ( SELECT 
                          		categ_rel.partner_id as partner_id,
                              array_to_string(array_agg(distinct categ.name ),' , ') as name
                            FROM res_partner_res_partner_category_rel categ_rel 
                            JOIN res_partner_category categ ON categ.id = categ_rel.category_id
                            GROUP BY categ_rel.partner_id) AS category
                      WHERE category.partner_id = partner.id) AS tags,
                    so.company_id as company_id
                FROM sale_order so
 				LEFT JOIN sale_order so_draft ON so_draft.id = so.id AND so_draft.state = 'draft' AND so_draft.invoice_status = 'no'
 				LEFT JOIN sale_order so_done ON so_done.id = so.id AND so_done.state not in ('draft','cancel') 
                LEFT JOIN res_partner partner ON partner.id = so.partner_id
                LEFT JOIN partner_pricelist p_list ON p_list.id = so.partner_pricelist_team_id
	  			GROUP BY 
                     partner.id,
                     partner.code,
                     so.user_id,
                     p_list.sales_admin_id,
                     so.payment_term_id,
                     so.company_id
				) AS main
                """ % (self._table)
        return request

    def get_main_request2(self):
        request = """
            CREATE or REPLACE VIEW %s AS
                SELECT 
                    main.*,
                     (COALESCE(main.amount_total,0) + COALESCE(main.amount_surat_jalan,0) + COALESCE(main.amount_residual,0)) AS total, 
                     (COALESCE(main.credit_limit_value,0) - (COALESCE(main.amount_total,0) + COALESCE(main.amount_surat_jalan,0) + COALESCE(main.amount_residual,0))) AS spare
                FROM 
				( with all_so as (

                    with product as (
                    SELECT
                        CONCAT(lpad(partner.id::TEXT, 5,'0'),rpad(p_list.sales_admin_id::TEXT,5,'0'))::BIGINT as id,
                        so.id as so_id,
                        partner.id AS partner_id,
                        partner.code AS partner_code,
                        so.user_id AS user_id,
                        p_list.sales_admin_id AS sales_admin_id,
                        so.payment_term_id AS payment_term_id,
                        sum(so.credit_limit_value) AS credit_limit_value,
                        sum(so_draft.amount_total) AS amount_total,
                                ( SELECT	
                                    sum(mv.amount_residual)
                                        FROM account_move mv
                                    WHERE mv.partner_id = partner.id AND mv.invoice_user_id = so.user_id) AS amount_residual,
                                ( SELECT name 
                                    FROM 
                                        ( SELECT 
                                                categ_rel.partner_id as partner_id,
                                                array_to_string(array_agg(distinct categ.name ),' , ') as name
                                                FROM res_partner_res_partner_category_rel categ_rel 
                                                JOIN res_partner_category categ ON categ.id = categ_rel.category_id
                                                GROUP BY categ_rel.partner_id) AS category
                                        WHERE category.partner_id = partner.id) AS tags,
                                        so.company_id as company_id
                                    FROM sale_order so
                            LEFT JOIN sale_order so_draft ON so_draft.id = so.id AND so_draft.state = 'draft' AND so_draft.invoice_status = 'no'
                                    LEFT JOIN res_partner partner ON partner.id = so.partner_id
                                    LEFT JOIN partner_pricelist p_list ON p_list.id = so.partner_pricelist_team_id
                                    GROUP BY 
                                        partner.id,
                                        partner.code,
                                        so.user_id,
                                        so.id,
                                        p_list.sales_admin_id,
                                        so.payment_term_id,
                                        so.company_id),

                                    so_done as (
                                select id as so_done_id, amount_total as amount_surat_jalan
                                from sale_order where invoice_status = 'to invoice') 

                            select * from product full join so_done on product.so_id = so_done.so_done_id
                                    )

                select * from all_so
				) AS main
                """ % (self._table)
        return request

    


    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request2())
