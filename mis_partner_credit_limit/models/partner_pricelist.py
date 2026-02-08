""" File partner pricelist"""
from odoo import api, fields, models, _, SUPERUSER_ID
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.exceptions import UserError



class InheritPartnerPricelist(models.Model):
    """ new object partner pricelist """
    _inherit = "partner.pricelist"

    def _compute_credit(self):
        print("===================PERHITUNGAN CREDIT INHERIT==============")
        """ 
            this function to give information over due
            this function to give information remaining credit
        """
        # Perubahan perhitungan current credit 19 Des 2022
        for this in self:
            partner = this.partner_id.id
            team_id = this.team_id.id
            over_due = 'not_overdue'
            credits = 0.0
            qwr = """
            -- SISA SO BLM RELEASE (STATUS: AKTIF) + SJ BLM INVOICE + INVOICE BLM BAYAR
            -- 1. SO AKTIF BLM RELEASE
            WITH so_active_not_release_yet AS (
            SELECT so.partner_id, so.name AS "so_no", pp.id AS "product_id", pt.name AS "product_name", sol.product_uom_qty AS "qty_so", sol.qty_delivered, (sol.product_uom_qty - sol.qty_delivered) AS "remaining_qty",
            ((sol.price_unit - sol.discount_fixed_line) * (sol.product_uom_qty - sol.qty_delivered)) AS "current_credit"
            FROM sale_order so LEFT JOIN sale_order_line sol ON so.id = sol.order_id
            LEFT JOIN product_product pp ON pp.id = sol.product_id
            LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
            WHERE so.state = 'sale'
            AND so.validity_date > CURRENT_DATE
            AND sol.price_unit <> 0
            ORDER BY product_id, ((sol.price_unit - sol.discount_fixed_line) * (sol.product_uom_qty - sol.qty_delivered)) DESC
            ),
            -- 2. SJ BLM INVOICE
            sj_not_invoice_yet AS (
            SELECT so.partner_id,so.name AS "so_no", sp.doc_name AS "sj_no",pp.id AS "product_id",pt.name AS "product_name", sm.product_uom_qty, coalesce(sm_return.product_uom_qty, 0) AS "qty_return",
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
            -- 3. INVOICE BLM BAYAR
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
                SELECT rp.id AS "partner_id", pp.team_id, rc.name AS "company_name", rp.name AS "customer_name", rp.code AS "customer_code", rp_sales.name AS "sales_name", rp_sales_admin.name AS "sales_admin_name",  apt.name AS "payment_term_name", pp.credit_limit
                FROM partner_pricelist pp LEFT JOIN res_company rc ON pp.company_id = rc.id
                    LEFT JOIN res_partner rp ON rp.id = pp.partner_id
                        LEFT JOIN res_users ru ON ru.id = pp.user_id 
                            LEFT JOIN res_partner rp_sales ON rp_sales.id = ru.partner_id
                                LEFT JOIN res_users ru_sa ON ru_sa.id = pp.sales_admin_id
                                    LEFT JOIN res_partner rp_sales_admin ON rp_sales_admin.id = ru_sa.partner_id
                                        LEFT JOIN account_payment_term apt ON apt.id = pp.payment_term_id
            )
            SELECT (SELECT sum(ppl.credit_limit) AS "all_credit_limit" FROM partner_pricelist ppl
            WHERE ppl.partner_id ="""+str(int(partner))+"""),SUM(current_credit) AS "current_credit"
            FROM (
                SELECT a.partner_id,'Sisa SO masih aktif' AS "Category",pd.division_id, pd.division_name, SUM(a.current_credit) AS "current_credit"
                FROM so_active_not_release_yet a LEFT JOIN product_division pd ON a.product_id = pd.id
                WHERE a.partner_id ="""+str(int(partner))+"""
                GROUP BY a.partner_id, pd.division_id, pd.division_name
                UNION
                SELECT a.partner_id,'SJ yang blm invoice' AS "Category", pd.division_id,pd.division_name, SUM(a.current_credit) AS "current_credit"
                FROM sj_not_invoice_yet a LEFT JOIN product_division pd ON a.product_id = pd.id
                WHERE a.partner_id = """+str(int(partner))+"""
                GROUP BY a.partner_id, pd.division_id, pd.division_name
                UNION
                SELECT a.partner_id,'Invoice belum terbayar' AS "Category",d.division_id,d.division_name, SUM(a.current_credit) AS "current_credit"
                FROM invoice_not_pay_yet a LEFT JOIN division d ON a.team_id = d.division_id
                WHERE a.partner_id = """+str(int(partner))+"""
                GROUP BY a.partner_id, d.division_id, d.division_name
            ) a LEFT JOIN partner_division pd ON ( a.division_id = pd.team_id AND a.partner_id = pd.partner_id)
            """
            self.env.cr.execute(qwr,())
            result = self.env.cr.dictfetchone()
            if result:
                print("result['current_credit']",result['current_credit'])
                credits += result['current_credit'] or 0.0

            # query sale without invoice
            # query = """
            #     select sum(b.price_total) as current_credit
            #     from sale_order a
            #     left join sale_order_line b on b.order_id = a.id
            #     where a.partner_id = %s and a.state in ('sale', 'done','forced_locked')  and a.team_id = %s and 
            #     NOT EXISTS (SELECT * FROM sale_order_line_invoice_rel WHERE b.id = sale_order_line_invoice_rel.order_line_id)
            #     and a.id in (select sale_id from stock_picking a 
            #                  left join stock_location b on a.location_dest_id = b.id 
            #                  where b.usage = 'customer' and a.state not in ('cancel', 'done','forced_locked') 
            #                  and a.sale_id is NOT NULL )
            # """
            # self.env.cr.execute(query, (partner, team_id,))
            # result = self.env.cr.dictfetchone()
            # if result:
            #     credits += result['current_credit'] or 0.0


            # # add by dion 22 juli 2020, to cover retur
            # query = """
            #     select sum(sm.product_uom_qty * sol.price_unit) as current_credit 
            #     from stock_move sm
            #             left join stock_picking sp on sm.picking_id = sp.id
            #             left join sale_order so on sp.sale_id = so.id
            #             left join stock_location sl on sp.location_dest_id = sl.id
            #             left join sale_order_line sol on sm.sale_line_id = sol.id
            #             where sl.usage ='internal' and sp.state in ('done') and sp.partner_id = %s and so.team_id = %s and sp.sale_id is NOT NULL;
            # """
            # self.env.cr.execute(query, (partner, team_id,))
            # result = self.env.cr.dictfetchone()
            # if result:
            #     credits -= result['current_credit'] or 0.0


            # # query sale use invoice
            # query = """
            #     select (coalesce(sum(inv.amount_residual),0)) as current_credit 
            #     from account_move inv where inv.id in (
            #     select distinct(e.id) as current_credit
            #     from sale_order a
            #     left join sale_order_line b on b.order_id = a.id
            #     left join sale_order_line_invoice_rel c on c.order_line_id = b.id
            #     left join account_move_line d on c.invoice_line_id = d.id
            #     left join account_move e on d.move_id = e.id and e.state in ('draft','posted') 
            #     where a.partner_id = %s and a.state in ('sale', 'done','forced_locked') and a.team_id = %s and e.type = 'out_invoice'
            #     )
            # """
            # self.env.cr.execute(query, (partner, team_id,))
            # result = self.env.cr.dictfetchone()
            # if result:
            #     credits += result['current_credit'] or 0.0
            # # query invoice without sale
            # query = """
            #     select (coalesce(sum(inv.amount_residual),0)) as current_credit 
            #     from account_move inv where inv.id in (
            #         select distinct(a.id)
            #         from account_move a
            #         left join account_move_line b on a.id = b.move_id
            #         left join sale_order_line_invoice_rel c on b.id = c.invoice_line_id
            #         where a.partner_id = %s and a.state in ('draft','posted','forced_locked') and a.team_id = %s and c.invoice_line_id = Null and inv.type = 'out_invoice'
            #     )
            # """
            # self.env.cr.execute(query, (partner, team_id,))
            # result = self.env.cr.dictfetchone()
            # if result:
            #     credits += result['current_credit'] or 0.0
            moveline_obj = self.env['account.move.line'].sudo()
            today_dt = datetime.now().date()

            # Check Over Due
            movelines = moveline_obj.search(
                [('partner_id', '=', partner), ('reconciled', '=', False),
                 ('move_id.type', '=', 'out_invoice'),
                 # menambahkan filter company ovdue sesuai company karena pada saat di sale order,
                 # notif overdue tidak sesuai
                 ('move_id.company_id', '=', self.env.company.id),
                 ('account_id.user_type_id.type', '=', 'receivable'),
                 ('move_id.team_id', '=', team_id),
                 ('move_id.state', '=', 'posted')
                 ]
            )
            movelines_over = movelines.filtered(lambda l: l.date_maturity < today_dt)
            
            # Check Over Due without link Invoice
            movelines2 = moveline_obj.search(
                [('partner_id', '=', partner), ('reconciled', '=', False),
                 ('move_id.type', '=', 'out_invoice'),
                 # menambahkan filter company ovdue sesuai company karena pada saat di sale order,
                 # notif overdue tidak sesuai
                 ('move_id.company_id', '=', self.env.company.id),
                 ('account_id.user_type_id.type', '=', 'receivable'),
                 # ('payment_id.invoice_ids.team_id', '=', team_id),
                 ('payment_id.state', '=', 'posted')
                 ]
            )
            movelines_over_2 = movelines2.filtered(lambda l: l.date_maturity < today_dt)
            # Query payment without invoice
            total_payment = sum(line.amount_residual for line in movelines2)
            
            if movelines_over or movelines_over_2:
                over_due = 'overdue'
            all_credit_limit = result['all_credit_limit']
            print("all_credit_limit", all_credit_limit)
            remaining_limit = all_credit_limit - credits - total_payment
            this.update({
                'over_due':over_due,
                'current_credit':credits + total_payment,
                'remaining_limit':remaining_limit
            })