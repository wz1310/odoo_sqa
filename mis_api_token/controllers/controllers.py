import functools
import logging
import datetime
import json
import werkzeug.wrappers
import ast

from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError, AccessDenied
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)
expires_in = "mis_api_token.expires_token_in"

def validate_token(func):
    """."""

    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        """."""
        access_token = request.httprequest.headers.get("access_token")
        if not access_token:
            # return invalid_response("access_token_not_found", "missing access token in request header", 401)
            return {'status':401,'state':'Failed','message':'missing access token in request header'}
            
        access_token_data = (
            request.env["mis.access.token"].sudo().search([("token", "=", access_token)], order="id DESC", limit=1)
        )

        if access_token_data.find_one_or_create_token(user_id=access_token_data.user_id.id) != access_token:
            # return self.invalid_response("access_token", "token seems to have expired or invalid", 401)
            return {'status':401,'state':'Failed','message':'token seems to have expired or invalid'}

        request.session.uid = access_token_data.user_id.id
        request.uid = access_token_data.user_id.id
        return func(self, *args, **kwargs)

    return wrap

_routes = ["/api/<model>", "/api/<model>/<id>", "/api/<model>/<id>/<action>"]

class Mistoken_api(http.Controller):
	def __init__(self):
		self._token = request.env["mis.access.token"]
		self._expires_in = request.env.ref(expires_in).sudo().value
		self._model = "ir.model"

	@http.route("/api/auth/token", methods=["GET"], type="http", auth="none", csrf=False)
	def token(self, **post):
		print("TEXXXXXXXXXXXXXXX")
		_token = request.env["mis.access.token"]
		params = ["db", "login", "password"]
		params = {key: post.get(key) for key in params if post.get(key)}
		db, username, password = (
			params.get("db"),
			post.get("login"),
			post.get("password"),
		)
		_credentials_includes_in_body = all([db, username, password])
		if not _credentials_includes_in_body:
			headers = request.httprequest.headers
			db = headers.get("db")
			username = headers.get("login")
			password = headers.get("password")
			_credentials_includes_in_headers = all([db, username, password])
			if not _credentials_includes_in_headers:
				return self.invalid_response(
					"missing error", "either of the following are missing [db, username,password]", 403,
				)
		try:
			request.session.authenticate(db, username, password)
		except AccessError as aee:
			return self.invalid_response("Access error", "Error: %s" % aee.name)
		except AccessDenied as ade:
			return self.invalid_response("Access denied", "Login, password or db invalid")
		except Exception as e:
			info = "The database name is not valid {}".format((e))
			error = "invalid_database"
			_logger.error(info)
			return self.invalid_response("wrong database name", error, 403)

		uid = request.session.uid
		if not uid:
			info = "authentication failed"
			error = "authentication failed"
			_logger.error(info)
			return self.invalid_response(401, error, info)

		access_token = _token.find_one_or_create_token(user_id=uid, create=True)
		expired = _token.sudo().search([("token", "=", access_token)])
		return werkzeug.wrappers.Response(
			status=200,
			content_type="application/json; charset=utf-8",
			headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
			response=json.dumps(
				{
					"state":"Success",
					"uid": uid,
					"name": request.env.user.name if uid else None,
					"user_context": request.session.get_context() if uid else {},
					"company_id": request.env.user.company_id.id if uid else None,
					"company_ids": request.env.user.company_ids.ids if uid else None,
					"access_token": access_token,
					"expires_in": expired.expires.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
				}
			),
		)

	def default(o):
		if isinstance(o, (datetime.date, datetime.datetime)):
			return o.isoformat()

	def valid_response(data, status=200):
		"""Valid Response
		This will be return when the http request was successfully processed."""
		data = {"state":"Success","count": len(data), "data": data}
		return werkzeug.wrappers.Response(
			status=status, content_type="application/json; charset=utf-8", response=json.dumps(data, default=default),
		)

	def valid_response2(typ, message=None, status=200):
		return werkzeug.wrappers.Response(
			status=status,
			content_type="application/json; charset=utf-8",
			headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
			response=json.dumps(
				{
					"state":"Success",
					"message": str(message),
				}
			),
		)

	def invalid_response(typ, message=None, status=401):
		return werkzeug.wrappers.Response(
			status=status,
			content_type="application/json; charset=utf-8",
			headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
			response=json.dumps(
				{
					"state":"Failed",
					"message": str(message)+" : "+str(status),
				}
			),
		)

	#select model
	@validate_token
	@http.route(_routes, type="json", auth="public", methods=["GET"], csrf=False)
	def api_get(self, model=None, id=None, **payload):
		param = json.loads(request.httprequest.data)
		ioc_name = model
		model = request.env[self._model].search([("model", "=", model)], limit=1)
		if model:
			domain=None
			fields=None
			offset=0
			limit=None
			order=None
			fields = ast.literal_eval(param['fields'])
			domain = ast.literal_eval(param['domain'])
			data = request.env[model.model].search_read(domain, fields, offset, limit, order)
			if data:
				return {'status':200,'state':'Success','count':len(data),'data':data}
		else:
			return {'status':404,'state':'Failed','message':"The model %s is not available in the registry." % ioc_name}

	#insert
	@validate_token
	@http.route("/api/<model>", type="json", auth="none", methods=["POST"], csrf=False)
	def post_data(self, model=None, id=None, **payload):
		payload = json.loads(request.httprequest.data)
		ioc_name = model
		model = request.env[self._model].search([("model", "=", model)], limit=1)
		values = {}
		if model:
			try:
				# changing IDs from string to int.
				for k, v in payload.items():
					if "__api__" in k:
						values[k[7:]] = ast.literal_eval(v)
					else:
						values[k] = v
				resource = request.env[model.model].create(values)
			except Exception as e:
				request.env.cr.rollback()
				respond={'status':401,'state':'Failed','message':e}
			else:
				data = resource.read()
				if resource:
					return {'status':200,'state':'Success','data':data}
				else:
					return {'status':200,'state':'Success','data':data}
		else:
			respond={'status':404,'state':'Failed','message':"The model %s is not available in the registry." % ioc_name}

		return respond

	#update
	@validate_token
	@http.route(_routes, type="json", auth="none", methods=["PUT"], csrf=False)
	def put_data(self, model=None, id=None, **payload):
		"""."""
		payload = json.loads(request.httprequest.data)
		_model = request.env[self._model].sudo().search([("model", "=", model)], limit=1)
		if not _model:
			respond={'status':404,'state':'Failed','message':"The model %s is not available in the registry." % model}
		else:
			if not payload['id']:
				respond={'status':401,'state':'Failed','message':"Id can`t empty !!"}
			else:
				try:
					domain=[('id','in',payload['id'])]
					_data=request.env[_model.model].sudo().search(domain)
					_data.write(payload['payload'])
				except Exception as e:
					request.env.cr.rollback()
					respond={'status':401,'state':'Failed','message':e}
				else:
					respond={'status':200,'state':'Success','message':"update %s record %s successfully!" % (_model.model,payload['id'])}
		return respond	

	#delete
	@validate_token
	@http.route(_routes, type="json", auth="none", methods=["DELETE"], csrf=False)
	def delete_data(self, model=None, id=None, **payload):
		"""."""
		_model = request.env[self._model].sudo().search([("model", "=", model)], limit=1)
		if not _model:
			respond={'status':404,'state':'Failed','message':"The model %s is not available in the registry." % model}
		else:
			try:
				payload = json.loads(request.httprequest.data)
				domain=[('id','in',payload['id'])]
				record = request.env[model].sudo().search(domain)
				if record:
					record.unlink()
				else:
					# return invalid_response("missing_record", "record object with id %s could not be found" % _id, 404,)
					respond={'status':401,'state':'Failed','message':'record object with id %s could not be found' % payload['id']}
			except Exception as e:
				request.env.cr.rollback()
				respond={'status':401,'state':'Failed','message':e}
			else:
				# return valid_response("record %s has been successfully deleted" % record.id)
				respond={'status':200,'state':'Success','message':"delete %s record %s successfully!" % (_model.model,payload['id'])}
		return respond

	#call function
	@validate_token
	@http.route("/api_function/<model>/<id>", type="http", auth="none", methods=["PATCH"], csrf=False)
	def patch(self, model=None, id=None, **payload):
		"""."""
		action = payload['action']
		try:
			_id = int(id)
		except Exception as e:
			return self.invalid_response("invalid literal %s for id with base " % id)
		try:
			record = request.env[model].sudo().search([("id", "=", _id)])
			_callable = action in [method for method in dir(record) if callable(getattr(record, method))]

			if record and _callable:
				getattr(record, action)()
			else:
				return self.invalid_response("record object with id %s could not be found or %s object has no method %s" % (_id, model, action))
		except Exception as e:
			return self.invalid_response(e)
		else:
			return self.valid_response2("record %s has been successfully patched" % record.id)

	@validate_token
	@http.route('/api/list_purchase_post', type='json', auth='user', methods=['POST'])
	def pr_list_event_post(self, **params):
		order = params.get("order")
		tanggal = order[0]['date_order']
		names = order[0]['name']
		order_type = order[0]['purchase_order_type']
		line_ids = order[0]['line_ids']
		states = order[0]['status']
		vals_line = []
		for x in line_ids:
			product_obj = request.env['product.product'].sudo().search([('default_code','=', x['product_id'])])
			vals_line.append((0,0,{
				'product_id': product_obj.id,
				'qty': x['qty'],
				}))
		vals_header = {
		'date_order': tanggal,'name': names,'state': states,'purchase_order_type': order_type,'line_ids':vals_line
		}
		pr_new = request.env['purchase.request'].sudo().create(vals_header)
		data = {
			'status':200,
			'message': 'success',
			'name' : pr_new.name,
			'purchase_order_type' : order_type,
			'date_order' : tanggal,
			'line_ids' : line_ids,		
		}
		return data



	


	

