# -*- coding: utf-8 -*-
# from odoo import http


# class MisAccountReports(http.Controller):
#     @http.route('/mis_account_reports/mis_account_reports/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mis_account_reports/mis_account_reports/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mis_account_reports.listing', {
#             'root': '/mis_account_reports/mis_account_reports',
#             'objects': http.request.env['mis_account_reports.mis_account_reports'].search([]),
#         })

#     @http.route('/mis_account_reports/mis_account_reports/objects/<model("mis_account_reports.mis_account_reports"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mis_account_reports.object', {
#             'object': obj
#         })
