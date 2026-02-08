import datetime
import json

from odoo import http
from odoo.http import request, JsonRequest, Response
from odoo.exceptions import AccessError, AccessDenied
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT,date_utils

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

    @http.route("/api/create_prs", type="json",auth='none', methods=["POST"], csrf=False)
    def create_pr(self, **payload):
        response={
        'status_code': '00',
        'status_message': 'success'
        }
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        db="SANQUA_WIM_TRIAL"
        login="odooapi"
        password="odooapi"
        request.session.authenticate(db,login,password)
        payload = json.loads(request.httprequest.data)
        pd_type, name_type = (payload.get("purchase_order_type"),payload.get("name"))
        validates = all([pd_type, name_type])
        if payload and validates:
            try:
                if payload['company_id'] == 1:
                    payload['company_id'] = 5
                elif payload['company_id'] == 2:
                    payload['company_id'] = 6
                elif payload['company_id'] == 5:
                    payload['company_id'] = 2
                elif payload['company_id'] == 6:
                    payload['company_id'] = 1
                entries = request.env['purchase.request'].sudo().create({
                    'name': payload['name'],
                    'date_order': payload['date_order'],
                    'company_id': payload['company_id'],
                    'purchase_order_type': payload['purchase_order_type'],
                    'user_sanqua': payload['user_sanqua'],
                    'no_fpb_sanqua': payload['no_fpb']
                 })
                if entries.purchase_order_type == 'asset':
                    entries.is_asset = 'True'
            except Exception as e:
                request.env.cr.rollback()
                respond={'status_code':-99,'status_msg':e}
            else:
                # data = resource.read()
                id_entries = int(entries)
                for x in payload['line_ids']:
                    product_obj = request.env['product.product'].sudo().search([('default_code','=', x['product_code'])])
                    item = request.env['purchase.request.line'].with_context(check_move_validity=False).sudo().create({
                        'purchase_request_id': id_entries,
                        'product_id': product_obj.id or False,
                        'qty': x['qty']
                     })
                entries.btn_submit()
                return response
        elif not validates:
            respond={'status_code':'-99','status_msg':'Mandatory field was empty!'}

        return respond