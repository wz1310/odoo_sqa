# -*- coding: utf-8 -*-
# from odoo import http


# class DnApi13(http.Controller):
#     @http.route('/dn_api_13/dn_api_13/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dn_api_13/dn_api_13/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('dn_api_13.listing', {
#             'root': '/dn_api_13/dn_api_13',
#             'objects': http.request.env['dn_api_13.dn_api_13'].search([]),
#         })

#     @http.route('/dn_api_13/dn_api_13/objects/<model("dn_api_13.dn_api_13"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dn_api_13.object', {
#             'object': obj
#         })
