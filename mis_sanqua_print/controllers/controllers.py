# -*- coding: utf-8 -*-
# from odoo import http


# class MisSanquaPrint(http.Controller):
#     @http.route('/mis_sanqua_print/mis_sanqua_print/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mis_sanqua_print/mis_sanqua_print/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mis_sanqua_print.listing', {
#             'root': '/mis_sanqua_print/mis_sanqua_print',
#             'objects': http.request.env['mis_sanqua_print.mis_sanqua_print'].search([]),
#         })

#     @http.route('/mis_sanqua_print/mis_sanqua_print/objects/<model("mis_sanqua_print.mis_sanqua_print"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mis_sanqua_print.object', {
#             'object': obj
#         })
