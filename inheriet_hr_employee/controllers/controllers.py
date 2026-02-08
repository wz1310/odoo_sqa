# -*- coding: utf-8 -*-
# from odoo import http


# class InherietHrEmployee(http.Controller):
#     @http.route('/inheriet_hr_employee/inheriet_hr_employee/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/inheriet_hr_employee/inheriet_hr_employee/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('inheriet_hr_employee.listing', {
#             'root': '/inheriet_hr_employee/inheriet_hr_employee',
#             'objects': http.request.env['inheriet_hr_employee.inheriet_hr_employee'].search([]),
#         })

#     @http.route('/inheriet_hr_employee/inheriet_hr_employee/objects/<model("inheriet_hr_employee.inheriet_hr_employee"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('inheriet_hr_employee.object', {
#             'object': obj
#         })
