# -*- coding: utf-8 -*-
# from odoo import http


# class MisReportSummaryPenjualanBersih(http.Controller):
#     @http.route('/mis_report_summary_penjualan_bersih/mis_report_summary_penjualan_bersih/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mis_report_summary_penjualan_bersih/mis_report_summary_penjualan_bersih/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mis_report_summary_penjualan_bersih.listing', {
#             'root': '/mis_report_summary_penjualan_bersih/mis_report_summary_penjualan_bersih',
#             'objects': http.request.env['mis_report_summary_penjualan_bersih.mis_report_summary_penjualan_bersih'].search([]),
#         })

#     @http.route('/mis_report_summary_penjualan_bersih/mis_report_summary_penjualan_bersih/objects/<model("mis_report_summary_penjualan_bersih.mis_report_summary_penjualan_bersih"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mis_report_summary_penjualan_bersih.object', {
#             'object': obj
#         })
