# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class StockCardReportWizard(models.TransientModel):
    _name = "aruskas.report.wizard"
    _description = "Arus Kas Report Wizard"

    date_from = fields.Date(string="Start Date",default=fields.Date.context_today)


    def button_export_html(self):
        self.ensure_one()
        action = self.env.ref("sanqua_proyeksi_aruskas.action_report_aruskas_report_html")
        vals = action.read()[0]
        context = vals.get("context", {})
        if context:
            context = safe_eval(context)
        model = self.env["report.aruskas.report"]
        report = model.create(self._prepare_stock_card_report())
        context["active_id"] = report.id
        context["active_ids"] = report.ids
        vals["context"] = context
        return vals

    def button_export_pdf(self):
        self.ensure_one()
        report_type = "qweb-pdf"
        return self._export(report_type)

    def button_export_xlsx(self):
        self.ensure_one()
        report_type = "xlsx"
        return self._export(report_type)

    def _prepare_stock_card_report(self):
        self.ensure_one()
        return {
            "date_from": self.date_from,
        }

    def _export(self, report_type):
        model = self.env["report.aruskas.report"]
        report = model.create(self._prepare_stock_card_report())
        return report.print_report(report_type)
