# -*- coding: utf-8 -*-
# from odoo import http


# class MisCompanyStockPicking(http.Controller):
#     @http.route('/mis_company_stock_picking/mis_company_stock_picking/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mis_company_stock_picking/mis_company_stock_picking/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mis_company_stock_picking.listing', {
#             'root': '/mis_company_stock_picking/mis_company_stock_picking',
#             'objects': http.request.env['mis_company_stock_picking.mis_company_stock_picking'].search([]),
#         })

#     @http.route('/mis_company_stock_picking/mis_company_stock_picking/objects/<model("mis_company_stock_picking.mis_company_stock_picking"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mis_company_stock_picking.object', {
#             'object': obj
#         })
