# -*- coding: utf-8 -*-
# from odoo import http


# class PundiPurchase(http.Controller):
#     @http.route('/pundi_purchase/pundi_purchase/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pundi_purchase/pundi_purchase/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pundi_purchase.listing', {
#             'root': '/pundi_purchase/pundi_purchase',
#             'objects': http.request.env['pundi_purchase.pundi_purchase'].search([]),
#         })

#     @http.route('/pundi_purchase/pundi_purchase/objects/<model("pundi_purchase.pundi_purchase"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pundi_purchase.object', {
#             'object': obj
#         })
