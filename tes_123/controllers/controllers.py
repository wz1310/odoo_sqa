# -*- coding: utf-8 -*-
# from odoo import http


# class Tes123(http.Controller):
#     @http.route('/tes_123/tes_123/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tes_123/tes_123/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tes_123.listing', {
#             'root': '/tes_123/tes_123',
#             'objects': http.request.env['tes_123.tes_123'].search([]),
#         })

#     @http.route('/tes_123/tes_123/objects/<model("tes_123.tes_123"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tes_123.object', {
#             'object': obj
#         })
