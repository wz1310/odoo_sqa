# -*- coding: utf-8 -*-
# from odoo import http


# class InherietHrDepartment(http.Controller):
#     @http.route('/inheriet_hr_department/inheriet_hr_department/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/inheriet_hr_department/inheriet_hr_department/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('inheriet_hr_department.listing', {
#             'root': '/inheriet_hr_department/inheriet_hr_department',
#             'objects': http.request.env['inheriet_hr_department.inheriet_hr_department'].search([]),
#         })

#     @http.route('/inheriet_hr_department/inheriet_hr_department/objects/<model("inheriet_hr_department.inheriet_hr_department"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('inheriet_hr_department.object', {
#             'object': obj
#         })
