# -*- coding: utf-8 -*-
# from odoo import http


# class ReportBersih(http.Controller):
#     @http.route('/report_bersih/report_bersih/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/report_bersih/report_bersih/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('report_bersih.listing', {
#             'root': '/report_bersih/report_bersih',
#             'objects': http.request.env['report_bersih.report_bersih'].search([]),
#         })

#     @http.route('/report_bersih/report_bersih/objects/<model("report_bersih.report_bersih"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('report_bersih.object', {
#             'object': obj
#         })
