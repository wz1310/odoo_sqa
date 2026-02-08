# -*- coding: utf-8 -*-
# from odoo import http


# class DnAccount(http.Controller):
#     @http.route('/dn_account/dn_account/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dn_account/dn_account/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('dn_account.listing', {
#             'root': '/dn_account/dn_account',
#             'objects': http.request.env['dn_account.dn_account'].search([]),
#         })

#     @http.route('/dn_account/dn_account/objects/<model("dn_account.dn_account"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dn_account.object', {
#             'object': obj
#         })
