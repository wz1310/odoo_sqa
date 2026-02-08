# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class ReportStockCardReportXlsx(models.AbstractModel):
    _name = "report.stock_card_report.report_stock_card_report_xlsx"
    _description = "Stock Card Report XLSX"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, objects):
        self._define_formats(workbook)
        for product in objects.product_ids:
            for ws_params in self._get_ws_params(workbook, data, product):
                ws_name = ws_params.get("ws_name")
                ws_name = self._check_ws_name(ws_name)
                ws = workbook.add_worksheet(ws_name)
                generate_ws_method = getattr(self, ws_params["generate_ws_method"])
                generate_ws_method(workbook, ws, ws_params, data, objects, product)

    def _get_ws_params(self, wb, data, product):
        filter_template = {
            "1_date_from": {
                "header": {"value": "Date from"},
                "data": {
                    "value": self._render("date_from"),
                    "format": self.format_tcell_date_center,
                },
            },
            "2_date_to": {
                "header": {"value": "Date to"},
                "data": {
                    "value": self._render("date_to"),
                    "format": self.format_tcell_date_center,
                },
            },
            "3_location": {
                "header": {"value": "Location"},
                "data": {
                    "value": self._render("location"),
                    "format": self.format_tcell_center,
                },
            },
        }
        initial_template = {
            "4_reference": {
                "data": {"value": "Saldo Awal", "format": self.format_tcell_center},
                "colspan": 4,
            },
            "94_all": {
                "data": {
                    "value": self._render("balance_qty"),
                    "format": self.format_tcell_amount_right,
                }
            },
            "95_all_price": {
                "data": {
                    "value": self._render("balance_price"),
                    "format": self.format_tcell_amount_right,
                }
            },
            "96_all_price": {
                "data": {
                    "value": self._render("balance_amount"),
                    "format": self.format_tcell_amount_right,
                }
            },
        }
        stock_card_template = {
            "1_date": {
                "header": {"value": "Date"},
                "data": {
                    "value": self._render("date"),
                    "format": self.format_tcell_date_left,
                },
                "width": 25,
            },
            "2_code": {
                "header": {"value": "Code"},
                "data": {
                    "value": self._render("code"),
                    "format": self.format_tcell_left,
                },
                "width": 25,
            },
            "3_product": {
                "header": {"value": "Product"},
                "data": {
                    "value": self._render("product"),
                    "format": self.format_tcell_left,
                },
                "width": 25,
            },
            "4_reference": {
                "header": {"value": "Reference"},
                "data": {
                    "value": self._render("reference"),
                    "format": self.format_tcell_left,
                },
                "width": 25,
            },
            "5_order": {
                "header": {"value": "No. Order"},
                "data": {
                    "value": self._render("order"),
                    "format": self.format_tcell_left,
                },
                "width": 25,
            },
            "6_input": {
                "header": {"value": "In Qty"},
                "data": {"value": self._render("input_qty")},
                "width": 25,
            },
            "7_input_price": {
                "header": {"value": "In Cost"},
                "data": {"value": self._render("input_cost")},
                "width": 25,
            },
            "8_input_price": {
                "header": {"value": "Nilai Masuk"},
                "data": {"value": self._render("input_amount")},
                "width": 25,
            },
           "91_output": {
                "header": {"value": "Out Qty"},
                "data": {"value": self._render("output_qty")},
                "width": 25,
            },
            "92_output_price": {
                "header": {"value": "Out Cost"},
                "data": {"value": self._render("output_cost")},
                "width": 25,
            },
            "93_output_price": {
                "header": {"value": "Nilai Keluar"},
                "data": {"value": self._render("out_amount")},
                "width": 25,
            },
            "94_all": {
                "header": {"value": "Qty Akhir"},
                "data": {"value": self._render("all_qty")},
                "width": 25,
            },
            "95_all_price": {
                "header": {"value": "Biaya/Unit"},
                "data": {"value": self._render("all_cost")},
                "width": 25,
            },
            "96_all_price": {
                "header": {"value": "Nilai Akhir"},
                "data": {"value": self._render("all_amount")},
                "width": 25,
            },
        }

        ws_params = {
            "ws_name": product.name,
            "generate_ws_method": "_stock_card_report",
            "title": "Stock Card - {}".format(product.name),
            "wanted_list_filter": [k for k in sorted(filter_template.keys())],
            "col_specs_filter": filter_template,
            "wanted_list_initial": [k for k in sorted(initial_template.keys())],
            "col_specs_initial": initial_template,
            "wanted_list": [k for k in sorted(stock_card_template.keys())],
            "col_specs": stock_card_template,
        }
        return [ws_params]

    def _stock_card_report(self, wb, ws, ws_params, data, objects, product):
        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers["standard"])
        ws.set_footer(self.xls_footers["standard"])
        self._set_column_width(ws, ws_params)
        # Title
        row_pos = 0
        row_pos = self._write_ws_title(ws, row_pos, ws_params, True)
        # Filter Table
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header",
            default_format=self.format_theader_blue_center,
            col_specs="col_specs_filter",
            wanted_list="wanted_list_filter",
        )
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="data",
            render_space={
                "date_from": objects.date_from or "",
                "date_to": objects.date_to or "",
                "location": objects.location_id.display_name or "",
            },
            col_specs="col_specs_filter",
            wanted_list="wanted_list_filter",
        )
        row_pos += 1
        # Stock Card Table
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header",
            default_format=self.format_theader_blue_center,
        )
        ws.freeze_panes(row_pos, 0)
        balance = objects._get_initial(
            objects.results.filtered(lambda l: l.product_id == product and l.is_initial)
        )
        balance_amount = objects._get_initial_balance(
            objects.results.filtered(lambda l: l.product_id == product and l.is_initial)
        )
        balance_price = 0.0
        if balance > 0.0:
            balance_price = balance_amount/balance
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="data",
            render_space={"balance_qty": balance,
                          "balance_amount": balance_amount,
                          "balance_price": balance_price},
            col_specs="col_specs_initial",
            wanted_list="wanted_list_initial",
        )
        product_lines = objects.results.filtered(
            lambda l: l.product_id == product and not l.is_initial
        )
        for line in product_lines:
            balance += line.product_in - line.product_out
            balance_amount += line.product_total_in - line.product_total_out
            all_cost = 0.0
            if balance > 0.0:
                all_cost = objects.truncate(balance_amount / balance)
           
            row_pos = self._write_line(
                ws,
                row_pos,
                ws_params,
                col_specs_section="data",
                render_space={
                    "date": line.date or "",
                    "code": line.code_product or "",
                    "product" : line.product_name or "",
                    "reference": line.reference or "",
                    "order": line.order or "",
                    "input_qty": line.product_in or "",
                    "output_qty": line.product_out or "",
                    "all_qty": balance,
                    "input_cost" : line.product_price_in or "",
                    "output_cost" : line.product_price_out or "",
                    "input_amount" : line.product_total_in or "",
                    "output_amount" : line.product_total_out or "",
                    "all_cost": all_cost,
                    "all_amount": balance_amount,

                },
                default_format=self.format_tcell_amount_right,
            )
