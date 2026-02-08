from odoo import fields, models, api, _
from datetime import datetime,timedelta,date
from odoo.exceptions import ValidationError,UserError
import datetime
import logging
import ast, json
_logger = logging.getLogger(__name__)
        

class PartnerPriceChangeRequest(models.Model):
    _name = 'partner.price.change.request'
    _description = "Partner Pricelist Change Request"
    _inherit = ["approval.matrix.mixin",'mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, copy=False, index=True, default=lambda self:self.env['ir.sequence'].next_by_code('seq.pp.change.request'),track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', 'Partner',
        ondelete='cascade', index=True, required=True,track_visibility='onchange')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submited', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('reject', 'Reject')
    ], string='State',default='draft',required=True, track_visibility='onchange')
    company_id = fields.Many2one('res.company', string="Company", required=True, ondelete="restrict", onupdate="restrict", default=lambda self:self.env.company.id, domain=False,track_visibility='onchange')
    line_ids = fields.One2many('partner.price.change.request.line', 'pp_change_request_id', string='Lines',track_visibility='onchange')
    old_line_ids = fields.One2many('old.partner.price.change.request.line', 'opp_change_request_id', track_visibility='onchange')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('seq.pp.change.request')
        result = super(PartnerPriceChangeRequest, self).create(vals)
        return result

    def unlink(self):
        if self.line_ids.ids:
            res = self.env.cr.execute("""DELETE FROM partner_price_change_request_line WHERE id in %s""",(tuple(self.line_ids.ids),))
        return super(PartnerPriceChangeRequest, self).unlink()

    def get_data(self):
        for this in self:
            partner = this.partner_id.id
            credits = 0.0
            qwr = """
            SELECT
            pps.id AS "p_pricelist_id",pps.partner_id AS "partner_id",pps.team_id AS "team_id",pps.user_id AS "user_id",
            pps.sales_admin_id AS "sales_admin_id",pps.credit_limit AS "credit_limit",
            (WITH so_active_not_release_yet AS (
                SELECT so.partner_id, so.name AS "so_no", pp.id AS "product_id", pt.name AS "product_name",
                sol.product_uom_qty AS "qty_so", sol.qty_delivered, (sol.product_uom_qty - sol.qty_delivered) AS "remaining_qty",
                ((sol.price_unit - sol.discount_fixed_line) * (sol.product_uom_qty - sol.qty_delivered)) AS "current_credit"
                FROM sale_order so LEFT JOIN sale_order_line sol ON so.id = sol.order_id
                LEFT JOIN product_product pp ON pp.id = sol.product_id
                LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                WHERE so.state = 'sale'
                AND so.validity_date > CURRENT_DATE
                AND sol.price_unit <> 0
                ORDER BY product_id, ((sol.price_unit - sol.discount_fixed_line) * (sol.product_uom_qty - sol.qty_delivered)) DESC
                ),
            sj_not_invoice_yet AS (SELECT so.partner_id,so.name AS "so_no", sp.doc_name AS "sj_no",pp.id AS "product_id",pt.name AS "product_name", sm.product_uom_qty,
                coalesce(sm_return.product_uom_qty, 0) AS "qty_return",
                (sm.product_uom_qty - coalesce(sm_return.product_uom_qty, 0) ) AS "qty_net",
                ((sm.product_uom_qty - coalesce(sm_return.product_uom_qty, 0) ) * (sol.price_unit - coalesce(sol.discount_fixed_line,0))
                    ) AS "current_credit"
                FROM stock_picking sp LEFT JOIN sale_order so ON sp.sale_id = so.id
                LEFT JOIN sale_order_line sol ON so.id = sol.order_id
                LEFT JOIN stock_move sm ON (sm.picking_id = sp.id AND sol.product_id = sm.product_id)
                LEFT JOIN product_product pp ON ( pp.id = sm.product_id)
                LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                LEFT JOIN stock_move sm_return ON ( sm.id = sm_return.origin_returned_move_id AND sm_return.state = 'done' )
                LEFT JOIN stock_picking_type AS spt ON sp.picking_type_id = spt.id
                WHERE sol.price_unit <> 0
                AND sp.invoice_id IS NULL
                AND spt.code IN ('outgoing') AND sp.state != 'cancel'
                AND sp.company_id = 2
                AND sp.location_dest_id = 5
                AND sp.doc_name <> 'New'
                AND sm.name not ilike 'Free %'
                ),
            invoice_not_pay_yet AS (
                SELECT id, partner_id,team_id, name, amount_residual_signed AS "current_credit"
                FROM account_move am
                WHERE company_id = 2
                AND type = 'out_invoice'
                AND amount_residual_signed <> 0
                AND state = 'posted'
                ORDER BY team_id
                ),
            product_division AS (
                SELECT pp.id, ct.id AS "division_id", ct.name AS "division_name", pc.name AS "category_name", pt.name AS "product_name"
                FROM crm_team ct LEFT JOIN crm_team_product_category_rel ctpc ON ct.id = ctpc.crm_team_id
                LEFT JOIN product_category pc ON pc.id = ctpc.product_category_id
                LEFT JOIN product_template pt ON pt.categ_id = pc.id
                LEFT JOIN product_product pp ON pp.product_tmpl_id = pt.id
                WHERE ct.company_id = 2
                AND ct.state = 'done'
                ),
            division AS (
                SELECT ct.id AS "division_id", ct.name AS "division_name"
                FROM crm_team ct
                WHERE ct.company_id = 2
                AND ct.state = 'done'
                ),
            partner_division AS (
                SELECT rp.id AS "partner_id", pp.team_id, rc.name AS "company_name", rp.name AS "customer_name",
                rp.code AS "customer_code", rp_sales.id AS "sales_id", rp_sales.name AS "sales_name",
                rp_sales_admin.name AS "sales_admin_name",  apt.name AS "payment_term_name",
                pp.credit_limit,pp.pricelist_id,pp.customer_group,pp.payment_term_id,pp.black_list
                FROM partner_pricelist pp LEFT JOIN res_company rc ON pp.company_id = rc.id
                LEFT JOIN res_partner rp ON rp.id = pp.partner_id
                LEFT JOIN res_users ru ON ru.id = pp.user_id
                LEFT JOIN res_partner rp_sales ON rp_sales.id = ru.partner_id
                LEFT JOIN res_users ru_sa ON ru_sa.id = pp.sales_admin_id
                LEFT JOIN res_partner rp_sales_admin ON rp_sales_admin.id = ru_sa.partner_id
                LEFT JOIN account_payment_term apt ON apt.id = pp.payment_term_id
                )
            SELECT SUM(current_credit) AS "current_credit"
            FROM (
                SELECT a.partner_id,'Sisa SO masih aktif' AS "Category",pd.division_id, pd.division_name,
                SUM(a.current_credit) AS "current_credit"
                FROM so_active_not_release_yet a LEFT JOIN product_division pd ON a.product_id = pd.id
                WHERE a.partner_id = pps.partner_id
                GROUP BY a.partner_id, pd.division_id, pd.division_name
                UNION
                SELECT a.partner_id,'SJ yang blm invoice' AS "Category", pd.division_id,pd.division_name, SUM(a.current_credit)AS "current_credit"
                FROM sj_not_invoice_yet a LEFT JOIN product_division pd ON a.product_id = pd.id
                WHERE a.partner_id = pps.partner_id
                GROUP BY a.partner_id, pd.division_id, pd.division_name
                UNION
                SELECT a.partner_id,'Invoice belum terbayar' AS "Category",d.division_id,d.division_name, SUM(a.current_credit) AS "current_credit"
                FROM invoice_not_pay_yet a LEFT JOIN division d ON a.team_id = d.division_id
                WHERE a.partner_id = pps.partner_id
                GROUP BY a.partner_id, d.division_id, d.division_name
                ) a LEFT JOIN partner_division pd ON( a.division_id = pd.team_id AND a.partner_id = pd.partner_id)),
            (SELECT
                CASE WHEN c.id_aml IS NOT NULL THEN 'overdue'
                END AS "overdue"
                FROM(
                    SELECT aml.id AS "id_aml"
                    FROM
                    account_move_line aml
                    LEFT JOIN account_move am ON aml.move_id = am.ID
                    LEFT JOIN account_account aa ON aa.ID = aml.account_id
                    LEFT JOIN account_account_type aat ON aat.ID = aa.user_type_id
                    WHERE
                    aml.partner_id = pps.partner_id 
                    AND aml.reconciled = FALSE
                    AND am.TYPE = 'out_invoice'
                    AND aat."type" = 'receivable'
                    AND am.team_id = pps.team_id
                    AND am.STATE = 'posted'
                    AND aml.date_maturity < NOW()::DATE
                    UNION
                    SELECT aml.id AS "id_aml"
                    FROM
                    account_move_line aml
                    LEFT JOIN account_move am ON aml.move_id = am.ID
                    LEFT JOIN account_account aa ON aa.ID = aml.account_id
                    LEFT JOIN account_account_type aat ON aat.ID = aa.user_type_id
                    LEFT JOIN account_payment ap ON ap.id = aml.payment_id
                    WHERE
                    aml.partner_id = pps.partner_id
                    AND aml.reconciled = FALSE
                    AND am.TYPE = 'out_invoice'
                    AND aat."type" = 'receivable'
                    AND am.team_id = pps.team_id
                    AND am.STATE = 'posted'
                    AND aml.date_maturity < NOW()::DATE
                    )c
                GROUP BY overdue),
                (SELECT ARRAY_AGG(str.user_id) AS "team_ids" FROM sales_team_users_rel str
                    LEFT JOIN res_users ru ON ru.id = str.user_id
                    LEFT JOIN crm_team ct ON ct.id = str.team_id
                    WHERE str.team_id = pps.team_id),
                pps.black_list AS "black_list",pps.pricelist_id AS "pricelist_id",
                pps.customer_group AS "customer_group",pps.payment_term_id AS "payment_term_id"
                FROM partner_pricelist pps
                WHERE partner_id =  """+str(int(partner))+"""            
            """
            self.env.cr.execute(qwr,())
            result = self.env.cr.dictfetchall()
            if result:
                for x in result:
                    this.old_line_ids = [(0,0,{
                        'partner_id':x['partner_id'],
                        'p_pricelist_id':x['p_pricelist_id'],
                        'team_id':x['team_id'],
                        'user_id':x['user_id'],
                        'sales_admin_id':x['sales_admin_id'],
                        'credit_limit':x['credit_limit'],
                        'current_credit':x['current_credit'],
                        'over_due':x['overdue'] if x['overdue'] else 'not_overdue',
                        'remaining_limit':sum([y['credit_limit'] if y['credit_limit'] else 0 for y in result])-int(x['current_credit'] if x['current_credit'] else 0),
                        'black_list':x['black_list'],
                        'pricelist_id':x['pricelist_id'],
                        'customer_group':x['customer_group'],
                        'payment_term_id':x['payment_term_id'],
                        'team_member_ids':x['team_ids']
                        })]
                    this.line_ids = [(0,0,{
                        'partner_id':x['partner_id'],
                        'p_pricelist_id':x['p_pricelist_id'],
                        'team_id':x['team_id'],
                        'user_id':x['user_id'],
                        'sales_admin_id':x['sales_admin_id'],
                        'credit_limit':x['credit_limit'],
                        'current_credit':x['current_credit'],
                        'over_due':x['overdue'] if x['overdue'] else 'not_overdue',
                        'remaining_limit':sum([y['credit_limit'] if y['credit_limit'] else 0 for y in result])-int(x['current_credit'] if x['current_credit'] else 0),
                        'black_list':x['black_list'],
                        'pricelist_id':x['pricelist_id'],
                        'customer_group':x['customer_group'],
                        'payment_term_id':x['payment_term_id'],
                        'team_member_ids':x['team_ids']
                        })]

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.old_line_ids = [(5,0)]
        self.line_ids = [(5,0)]
        self.get_data()

    def btn_submit(self):
        self.checking_approval_matrix()
        self.state = 'submited'

    def btn_approve(self):
        self.approving_matrix()
        if self.line_ids:
            for x in self.line_ids:
                self.env.cr.execute("""UPDATE partner_pricelist
                    SET
                    "team_id" =  """+str(int(x.team_id))+""",
                    "user_id" =  """+str(int(x.user_id))+""",
                    "sales_admin_id" =  """+str(int(x.sales_admin_id))+""",
                    "credit_limit" =  """+str(int(x.credit_limit))+""",
                    "pricelist_id" =  """+str(int(x.pricelist_id))+""",
                    "customer_group" =  """+str(int(x.customer_group))+""",
                    "payment_term_id" =  """+str(int(x.payment_term_id))+"""
                    WHERE
                    id = """+str(int(x.p_pricelist_id))+"""
                    """)
        self.state = 'approved'

    def btn_reject(self):
        self.state = 'reject'
        self.rejecting_matrix()

    def btn_draft(self):
        self.state = 'draft'

class PartnerPricehangeRequestLine(models.Model):
    _name = 'partner.price.change.request.line'
    _description = "Partner Price Change Request Line"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    pp_change_request_id = fields.Many2one('partner.price.change.request', string='Partner Price Change Request')
    p_pricelist_id = fields.Integer('Partner Pricelist ID')
    partner_id = fields.Many2one('res.partner', 'Partner')
    team_id = fields.Many2one('crm.team', 'Divisi', index=True, required=True)
    team_member_ids = fields.Many2many('res.users')

    user_id = fields.Many2one('res.users', string='Salesperson')
    credit_limit = fields.Float('Credit Limit', required=True, default=0.0)
    current_credit = fields.Float("Current Credit")
    over_due = fields.Selection(string='Over Due',
        selection=[('not_overdue', 'Not Over Due'), ('overdue', 'Over Due')])
    remaining_limit = fields.Float("Remaining Limit")
    black_list = fields.Selection(string='Status BlackList',
        selection=[('not_blacklist', 'Not Black List'), ('blacklist', 'Black List')])
    pricelist_id = fields.Many2one('product.pricelist',string='Pricelist')
    customer_group = fields.Many2one('customer.group',string='Customer Group')
    payment_term_id = fields.Many2one('account.payment.term',string='Terms Of Payment')
    sales_admin_id = fields.Many2one('res.users', string='Sales admin')

class PartnerPricehangeRequestLine(models.Model):
    _name = 'old.partner.price.change.request.line'
    _description = "Partner Price Change Request Line"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    opp_change_request_id = fields.Many2one('partner.price.change.request', string='Partner Price Change Request')
    p_pricelist_id = fields.Integer('Partner Pricelist ID')
    partner_id = fields.Many2one('res.partner', 'Partner')
    team_id = fields.Many2one('crm.team', 'Divisi', index=True, required=True)
    team_member_ids = fields.Many2many('res.users')

    user_id = fields.Many2one('res.users', string='Salesperson')
    credit_limit = fields.Float('Credit Limit', required=True, default=0.0)
    current_credit = fields.Float("Current Credit")
    over_due = fields.Selection(string='Over Due',
        selection=[('not_overdue', 'Not Over Due'), ('overdue', 'Over Due')])
    remaining_limit = fields.Float("Remaining Limit")
    black_list = fields.Selection(string='Status BlackList',
        selection=[('not_blacklist', 'Not Black List'), ('blacklist', 'Black List')])
    pricelist_id = fields.Many2one('product.pricelist',string='Pricelist')
    customer_group = fields.Many2one('customer.group',string='Customer Group')
    payment_term_id = fields.Many2one('account.payment.term',string='Terms Of Payment')
    sales_admin_id = fields.Many2one('res.users', string='Sales admin')