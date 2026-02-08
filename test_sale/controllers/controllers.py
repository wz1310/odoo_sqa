# import json
# import requests
# from odoo.tests import Form
# import werkzeug.wrappers

# from odoo import api, models, fields, _
# from odoo import http, _, exceptions
# from odoo.http import content_disposition, request, Response
# import io
# import xlsxwriter


# class TestApi(http.Controller):
# 	@http.route('/api/list_purchase_post', type='json', auth='user', methods=['POST'])
# 	def pr_list_event_post(self, **params):
# 		order = params.get("order")
# 		tanggal = order[0]['date_order']
# 		names = order[0]['name']
# 		order_type = order[0]['purchase_order_type']
# 		line_ids = order[0]['line_ids']
# 		states = order[0]['status']
# 		vals_line = []
# 		for x in line_ids:
# 			product_obj = request.env['product.product'].sudo().search([('default_code','=', x['product_id'])])
# 			vals_line.append((0,0,{
# 				'product_id': product_obj.id,
# 				'qty': x['qty'],
# 				}))
# 		vals_header = {
# 		'date_order': tanggal,'name': names,'state': states,'purchase_order_type': order_type,'line_ids':vals_line
# 		}
# 		request.env['purchase.request'].sudo().create(vals_header)
# 		data = {
# 			'status':200,
# 			'message': 'success',
# 			'purchase_order_type' : order_type,
# 			'date_order' : tanggal,
# 			'line_ids' : line_ids,		
# 		}
# 		return data

# 	@http.route('/web/session/authenticate', type='json', auth='none', csrf=False)
# 	def authenticate(self, db,login,password,base_location=None):
# 		request.session.authenticate(db,login,password)
# 		return request.env['ir.http'].session_info()

# 	@http.route('/api/authenticate',methods=["GET"], type='http', auth='none', csrf=False)
# 	def auth_api(self):
# 		headers = request.httprequest.headers
# 		db = headers.get("db")
# 		login = headers.get("login")
# 		password = headers.get("password")
# 		request.session.authenticate(db,login,password)
# 		data = {
# 			'status':200,
# 			'message': 'success'}
# 		return werkzeug.wrappers.Response(
# 			status=200,
# 			content_type="application/json; charset=utf-8",
# 			response=json.dumps(data))

# 	@http.route('/api/my_auth',type='json', auth='none', methods=["POST"], csrf=False)
# 	def authenticate(self, *args, **post):
# 		try:
# 			login = post["login"]
# 		except KeyError:
# 			raise exceptions.AccessDenied(message='`login` is required.')
# 		try:
# 			password = post["password"]
# 		except KeyError:
# 			raise exceptions.AccessDenied(message='`password` is required.')
# 		try:
# 			db = post["db"]
# 		except KeyError:
# 			raise exceptions.AccessDenied(message='`db` is required.')
# 		http.request.session.authenticate(db, login, password)
# 		res = request.env['ir.http'].session_info()
# 		return res		