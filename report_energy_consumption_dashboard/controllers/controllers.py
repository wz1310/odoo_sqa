# -*- coding: utf-8 -*-
# from odoo import http


# class ReportEnergyConsumptionDashboard(http.Controller):
#     @http.route('/report_energy_consumption_dashboard/report_energy_consumption_dashboard/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/report_energy_consumption_dashboard/report_energy_consumption_dashboard/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('report_energy_consumption_dashboard.listing', {
#             'root': '/report_energy_consumption_dashboard/report_energy_consumption_dashboard',
#             'objects': http.request.env['report_energy_consumption_dashboard.report_energy_consumption_dashboard'].search([]),
#         })

#     @http.route('/report_energy_consumption_dashboard/report_energy_consumption_dashboard/objects/<model("report_energy_consumption_dashboard.report_energy_consumption_dashboard"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('report_energy_consumption_dashboard.object', {
#             'object': obj
#         })
