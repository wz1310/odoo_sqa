import datetime
import json

from odoo import http
from odoo.http import request, JsonRequest, Response
from odoo.exceptions import AccessError, AccessDenied
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT,date_utils
import ast

_routes = ["/api/<model>", "/api/<model>/<id>", "/api/<model>/<id>/<action>"]

def alternative_json_response(self, result=None, error=None):
    if error is not None:
        response = error
    if result is not None:
        response = result
    mime = 'application/json'
    body = json.dumps(response, default=date_utils.json_default)
    return Response(
        body, status=error and error.pop('http_status', 200) or 200,
         headers=[('Content-Type', mime), ('Content-Length', len(body))]
         )

class NewApiPr(http.Controller):

    def __init__(self):
        self._model = "ir.model"

    @http.route(_routes, type="json",auth='none', methods=["GET"], csrf=False)
    def get_data(self,model=None, id=None, **payload):
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        params = ["db", "login", "password"]
        params = {key: payload.get(key) for key in params if payload.get(key)}
        db, username, password = (
            params.get("db"),
            payload.get("login"),
            payload.get("password"),
        )
        company_id = payload.get("company_id")
        if company_id:
            request.env['res.users'].sudo().search([('login','=',payload.get("login"))]).sudo().write({'company_id':payload.get("company_id")})
        _credentials_includes_in_body = all([db, username, password])
        if _credentials_includes_in_body:
            try:
                request.session.authenticate(db, username, password)
                ioc_name = model
                model = request.env[self._model].search([("model", "=", model)], limit=1)
                if model:
                    domain=None
                    fields=None
                    fields = ast.literal_eval(payload['fields'])
                    domain = ast.literal_eval(payload['domain'])
                    allow_company = payload.get("allow_company")
                    data = request.env[model.model].with_context(allowed_company_ids=[x for x in allow_company]).search_read(domain, fields)
                    if data:
                        response={'status_code': '00','status_message': 'success', 'count':len(data),'data':data}
                    else:
                        response={'status_code':'-99','status_msg':'No Data'}
                else:
                    response={'status_code':'-99','status_msg':'No Model :%s' % ioc_name}
            except:
                response={'status_code':'-99','status_msg':'Connection refused!'}
        else:
            response={'status_code':'-99','status_msg':'Mandatory field was empty!'}
        return response