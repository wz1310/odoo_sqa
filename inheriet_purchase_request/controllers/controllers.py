# -*- coding: utf-8 -*-
# from odoo import http


# class InherietPurchaseRequest(http.Controller):
#     @http.route('/inheriet_purchase_request/inheriet_purchase_request/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/inheriet_purchase_request/inheriet_purchase_request/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('inheriet_purchase_request.listing', {
#             'root': '/inheriet_purchase_request/inheriet_purchase_request',
#             'objects': http.request.env['inheriet_purchase_request.inheriet_purchase_request'].search([]),
#         })

#     @http.route('/inheriet_purchase_request/inheriet_purchase_request/objects/<model("inheriet_purchase_request.inheriet_purchase_request"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('inheriet_purchase_request.object', {
#             'object': obj
#         })
