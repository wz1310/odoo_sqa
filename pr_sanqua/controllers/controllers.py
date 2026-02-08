# -*- coding: utf-8 -*-
# from odoo import http


# class PrSanqua(http.Controller):
#     @http.route('/pr_sanqua/pr_sanqua/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pr_sanqua/pr_sanqua/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pr_sanqua.listing', {
#             'root': '/pr_sanqua/pr_sanqua',
#             'objects': http.request.env['pr_sanqua.pr_sanqua'].search([]),
#         })

#     @http.route('/pr_sanqua/pr_sanqua/objects/<model("pr_sanqua.pr_sanqua"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pr_sanqua.object', {
#             'object': obj
#         })
