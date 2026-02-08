# -*- coding: utf-8 -*-
# from odoo import http


# class InherietBudgetControl(http.Controller):
#     @http.route('/inheriet_budget_control/inheriet_budget_control/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/inheriet_budget_control/inheriet_budget_control/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('inheriet_budget_control.listing', {
#             'root': '/inheriet_budget_control/inheriet_budget_control',
#             'objects': http.request.env['inheriet_budget_control.inheriet_budget_control'].search([]),
#         })

#     @http.route('/inheriet_budget_control/inheriet_budget_control/objects/<model("inheriet_budget_control.inheriet_budget_control"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('inheriet_budget_control.object', {
#             'object': obj
#         })
