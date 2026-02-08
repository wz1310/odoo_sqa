# -*- coding: utf-8 -*-
# from odoo import http


# class InherietJournalPayment(http.Controller):
#     @http.route('/inheriet_journal_payment/inheriet_journal_payment/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/inheriet_journal_payment/inheriet_journal_payment/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('inheriet_journal_payment.listing', {
#             'root': '/inheriet_journal_payment/inheriet_journal_payment',
#             'objects': http.request.env['inheriet_journal_payment.inheriet_journal_payment'].search([]),
#         })

#     @http.route('/inheriet_journal_payment/inheriet_journal_payment/objects/<model("inheriet_journal_payment.inheriet_journal_payment"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('inheriet_journal_payment.object', {
#             'object': obj
#         })
