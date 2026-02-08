# -*- coding: utf-8 -*-
# from odoo import http


# class ExpensesRequest(http.Controller):
#     @http.route('/expenses_request/expenses_request/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/expenses_request/expenses_request/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('expenses_request.listing', {
#             'root': '/expenses_request/expenses_request',
#             'objects': http.request.env['expenses_request.expenses_request'].search([]),
#         })

#     @http.route('/expenses_request/expenses_request/objects/<model("expenses_request.expenses_request"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('expenses_request.object', {
#             'object': obj
#         })
