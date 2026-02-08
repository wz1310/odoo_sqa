# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockCardView(models.TransientModel):
    _name = "aruskas.view"
    _description = "Stock Card View"
    _order = "date"

    date = fields.Datetime()
    company_id = fields.Many2one(comodel_name="res.company")
    bank_kas = fields.Float()
    piutang = fields.Float()
    hutang = fields.Float()
    budget = fields.Float()
    akhir = fields.Float(compute="hitung")

    def hitung(self):
        for this in self:
            this.akhir = this.bank_kas + this.piutang - this.hutang - this.budget


class StockCardReport(models.TransientModel):
    _name = "report.aruskas.report"
    _description = "Stock Card Report"

    # Filters fields, used for data computation
    date_from = fields.Date()
    # company_id = fields.Many2one(comodel_name="res.company")

    # Data fields, used to browse report data
    results = fields.Many2many(
        comodel_name="aruskas.view",
        compute="_compute_results",
        help="Use compute fields, so there is nothing store in database",
    )

    def _compute_results(self):
        self.ensure_one()
        date_from = self.date_from or fields.Date.context_today(self)
        
        # product_filter = ""
        # if self.company_id:
        #     if len(self.company_id) == 1:
        #         product_tuple = "(%s)" % self.company_id.id
        #     else:
        #         product_tuple = tuple(self.company_id.ids)
        #     product_filter = (" AND move.company_id IN %s") % (str(product_tuple))

        self._cr.execute(
            """
           SELECT move.company_id as company_id,
            sum(move.balance) as bank_kas,
            (SELECT sum(move_p.amount_residual) as bank_kas
            FROM account_move move_p
            WHERE move_p.invoice_date_due < %s AND move_p.type = 'out_invoice' AND move_p.company_id = move.company_id
            GROUP BY move_p.company_id) as piutang,
            (SELECT sum(move_p.amount_residual) as bank_kas
            FROM account_move move_p
            WHERE move_p.invoice_date_due < %s AND move_p.type = 'in_invoice' AND move_p.company_id = move.company_id
            GROUP BY move_p.company_id) as hutang,
            (SELECT sum(a.planned_amount) FROM crossovered_budget_lines a
            LEFT JOIN crossovered_budget b ON b.id = a.crossovered_budget_id
            WHERE a.date_from <= %s AND a.date_to >= %s AND b.state in ('done','validate')
            AND a.company_id = move.company_id GROUP BY a.company_id) as budget
            FROM account_move_line move
            LEFT JOIN account_account aa ON aa.id = move.account_id
            LEFT JOIN account_account_type c ON c.id = aa.user_type_id 
            WHERE c.name ilike 'Bank and Cash' AND move.date <= %s
            GROUP BY move.company_id
        """,
            (
                date_from,
                date_from,
                date_from,
                date_from,
                date_from,
            ),
        )
        stock_card_results = self._cr.dictfetchall()
        ReportLine = self.env["aruskas.view"]
        self.results = [ReportLine.new(line).id for line in stock_card_results]

    def print_report(self, report_type="qweb"):
        self.ensure_one()
        action = (
            report_type == "xlsx"
            and self.env.ref("sanqua_proyeksi_aruskas.action_aruskas_report_xlsx")
            or self.env.ref("sanqua_proyeksi_aruskas.action_aruskas_report_pdf")
        )
        return action.report_action(self, config=False)

    def _get_html(self):
        result = {}
        rcontext = {}
        report = self.browse(self._context.get("active_id"))
        if report:
            rcontext["o"] = report
            result["html"] = self.env.ref(
                "sanqua_proyeksi_aruskas.report_aruskas_report_html"
            ).render(rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self.with_context(given_context)._get_html()
