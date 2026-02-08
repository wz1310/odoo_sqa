import datetime
import json
import requests

from odoo import http
from odoo.http import request, JsonRequest, Response
from odoo.exceptions import AccessError, AccessDenied
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT,date_utils
from datetime import datetime, timedelta
from odoo import models, fields, api, SUPERUSER_ID, _

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
        
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        # db="SANQUA_LIVE_16032022"
        db_name = request.env['ir.config_parameter'].sudo().search([('key','=','api_db_name')])
        usr_login = request.env['ir.config_parameter'].sudo().search([('key','=','api_login_name')])
        usr_pass = request.env['ir.config_parameter'].sudo().search([('key','=','api_login_pass')])
        db=db_name.value
        login=usr_login.value
        password=usr_pass.value
        request.session.authenticate(db,login,password)
        payload = json.loads(request.httprequest.data)
        pd_type, name_type = (payload.get("purchase_order_type"),payload.get("name"))
        validates = all([pd_type, name_type])
        entries = False
        if payload and validates:
            product_by_project = request.env['product.product'].sudo().search([('default_code','=', payload['odoo_project_code'])])
            try:
                if payload['company_id'] == 1:
                    payload['company_id'] = 5
                elif payload['company_id'] == 2:
                    payload['company_id'] = 6
                elif payload['company_id'] == 5:
                    payload['company_id'] = 2
                elif payload['company_id'] == 6:
                    payload['company_id'] = 1
                for x in payload['line_ids']:
                    if not payload['odoo_project_code'] and not x['product_code']:
                        respond={'status_code':-99,'status_msg':"Kode produk tidak boleh kosong"}
                        return respond
                    product_obj = request.env['product.product'].sudo().search([('default_code','=', x['product_code'])])
                    if len(product_obj.mapped('default_code'))>1 and not product_by_project and not payload['odoo_project_code']:
                        db_pr = request.env['product.product'].sudo().search([('default_code','in', [x['product_code'] for x in payload['line_ids']])]).mapped('default_code')
                        duplicate = [x for x  in db_pr if db_pr.count(x)>1]
                        response={'status_code':-99,'status_msg':"Product code %s is double.."%(list(set(duplicate)))}
                        return response
                    if not product_obj and not product_by_project and not payload['odoo_project_code']:
                        db_pr = request.env['product.product'].sudo().search([]).mapped('default_code')
                        no_prod = [x['product_code'] for x in payload['line_ids'] if x['product_code'] not in db_pr]
                        response={'status_code':-99,'status_msg':"Product code %s not exist.."%(no_prod)}
                        return response
                entries = request.env['purchase.request'].with_context(force_company=payload['company_id']).sudo().create({
                # entries = request.env['purchase.request'].sudo().create({
                    'name': payload['name'],
                    'date_order': payload['date_order'],
                    'company_id': payload['company_id'],
                    'purchase_order_type': payload['purchase_order_type'],
                    'user_sanqua': payload['user_sanqua'],
                    'no_fpb_sanqua': payload['no_fpb'],
                    'state': payload['status']
                 })
                # print("ID PR", entries.id)
                if entries.purchase_order_type == 'asset':
                    entries.is_asset = 'True'

                response={
                    'status_code': '00',
                    'status_message': 'success',
                    'name': entries.name
                }
            except Exception as e:
                request.env.cr.rollback()
                respond={'status_code':-99,'status_msg':e}
            else:
                # data = resource.read()
                id_entries = int(entries)
                for x in payload['line_ids']:
                    # if len(product_obj.mapped('default_code'))>1:
                    #     db_pr = request.env['product.product'].sudo().search([('default_code','in', [x['product_code'] for x in payload['line_ids']])]).mapped('default_code')
                    #     duplicate = [x for x  in db_pr if db_pr.count(x)>1]
                    #     response={'status_code':-99,'status_msg':"Product code %s is double.."%(list(set(duplicate)))}
                    #     return response                        
                    # if not product_obj:
                    #     db_pr = request.env['product.product'].sudo().search([]).mapped('default_code')
                    #     no_prod = [x['product_code'] for x in payload['line_ids'] if x['product_code'] not in db_pr]
                    #     response={'status_code':-99,'status_msg':"Product code %s not exist.."%(no_prod)}
                    #     return response
                    if not payload['odoo_project_code']:
                        product_obj = request.env['product.product'].sudo().search([('default_code','=', x['product_code'])])
                        item = request.env['purchase.request.line'].with_context(check_move_validity=False).sudo().create({
                            'purchase_request_id': id_entries,
                            'product_id': product_obj.id,
                            'qty': x['qty'],
                            'desc': x['product_name'],
                            'fpb_not': x['note'],
                            'fpb_uom': product_obj.uom_id.id
                            })
                    elif payload['odoo_project_code']:
                        product_obj = request.env['product.product'].sudo().search([('default_code','=', x['product_code'])])
                        uom_null = request.env['uom.uom'].sudo().search([('name','ilike', x['uom'])],limit=1)
                        product_by_project = request.env['product.product'].sudo().search([('default_code','=', payload['odoo_project_code'])])
                        if product_by_project:
                            if not x['product_code'] and not uom_null:
                                respond={'status_code':-99,'status_msg':x['uom']+' '+"not exist.."}
                                return respond
                            item = request.env['purchase.request.line'].with_context(check_move_validity=False).sudo().create({
                                'purchase_request_id': id_entries,
                                'product_id': product_by_project.id,
                                'qty': x['qty'],
                                'desc': x['product_name'],
                                'fpb_not': x['note'],
                                'fpb_uom': product_obj.uom_id.id if x['product_code'] else uom_null.id
                                })
                        elif not product_by_project:
                            respond={'status_code':-99,'status_msg':payload['odoo_project_code']+' '+"not exist.."}
                            return respond
                if entries.purchase_order_type in ['bahan_baku','amdk']:
                    entries.btn_submit()
                else:
                    entries._api_validate()
                    request.cr.execute("""UPDATE purchase_request
                        SET
                        "state" = 'approved'
                        WHERE
                        id = """+str(int(entries.id))+"""
                        """)
                    entries.line_ids.approve()
                return response
        elif not validates:
            respond={'status_code':'-99','status_msg':'Mandatory field was empty!'}

        return respond

    @http.route("/api/cancel_prs", type="json",auth='none', methods=["POST"], csrf=False)
    def cancel_prs(self, **payload):
        
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        # db="SANQUA_LIVE_16032022"
        db_name = request.env['ir.config_parameter'].sudo().search([('key','=','api_db_name')])
        usr_login = request.env['ir.config_parameter'].sudo().search([('key','=','api_login_name')])
        usr_pass = request.env['ir.config_parameter'].sudo().search([('key','=','api_login_pass')])
        db=db_name.value
        login=usr_login.value
        password=usr_pass.value
        request.session.authenticate(db,login,password)
        payload = json.loads(request.httprequest.data)
        pd_name,pd_reason = (payload.get("pr_name"),payload.get("reason"))
        validates = all([pd_name,pd_reason])
        if payload and validates:
            try:
                query = """
                UPDATE purchase_request SET status_pr = 'cancel'
                ,cancel_details = %s
                WHERE name IN %s RETURNING ID"""
                request._cr.execute(query, (payload['reason'],tuple(payload['pr_name'].split(',')),))
                result = request.env.cr.dictfetchall()
                print("RESULLLL", result)
                msgs = []
                msgs.append("PR has canceled from FPB")
                if result:
                    for x in result:
                        request.env['purchase.request'].search([('id','=',x['id'])]).message_post(body=msgs[0])
                response={
                    'status_code': '00',
                    'status_message': 'success'
                }
                return response
            except Exception as e:
                request.env.cr.rollback()
                respond={'status_code':-99,'status_msg':e}
        elif not validates:
            respond={'status_code':'-99','status_msg':'Mandatory field was empty!'}

        return respond

    @http.route("/api/cek_produk", type="json",auth='none', methods=["POST"], csrf=False)
    def cek_produk(self, **payload):
        
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        # db="SANQUA_LIVE_16032022"
        db_name = request.env['ir.config_parameter'].sudo().search([('key','=','api_db_name')])
        usr_login = request.env['ir.config_parameter'].sudo().search([('key','=','api_login_name')])
        usr_pass = request.env['ir.config_parameter'].sudo().search([('key','=','api_login_pass')])
        db=db_name.value
        login=usr_login.value
        password=usr_pass.value
        request.session.authenticate(db,login,password)
        payload = json.loads(request.httprequest.data)
        items = (payload.get("items"))
        validates = all([items])
        if payload and validates:
            try:
                for x in payload['items']:
                    # product_obj = request.env['product.product'].sudo().search([('default_code','=', x['code']),('name','=', x['name']),('uom_id.name','=', x['uom'])])
                    if payload:
                        # have_uom = request.env['uom.uom'].sudo().search([('name','ilike',x['uom'])],limit=1)
                        sql = """SELECT name FROM uom_uom"""
                        request.env.cr.execute(sql,())
                        result_uom = request.env.cr.dictfetchall()
                        # print("RESULLLL",tuple([x['code'] for x in payload['items']]))

                        sql = """SELECT default_code FROM product_product
                        WHERE default_code in """+str(tuple([x['code'] for x in payload['items']]))+""" """
                        request.env.cr.execute(sql,())
                        result_dobel_code = request.env.cr.dictfetchall()
                        print("result_dobel_code",result_dobel_code)

                        # db_uom = request.env['uom.uom'].sudo().search([])
                        db_uom = [x['name'] for x in result_uom]

                        # dbel_pr_code = request.env['product.product'].sudo().search([('default_code','in', [x['code'] for x in payload['items']])]).mapped('default_code')
                        # duplicate_code = [x for x  in dbel_pr_code if dbel_pr_code.count(x)>1]
                        dbel_pr_code = [x['default_code'] for x in result_dobel_code]
                        duplicate_code = [x for x  in dbel_pr_code if dbel_pr_code.count(x)>1]
                        print("duplicate_code",duplicate_code)


                        sql = """SELECT pt.name FROM product_product pp
                        LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
                        WHERE pt.name in """+str(tuple([x['name'] for x in payload['items']]))+""" """
                        request.env.cr.execute(sql,())
                        result_dobel_name = request.env.cr.dictfetchall()
                        print("result_dobel_name",result_dobel_name)

                        # dbel_pr_name = request.env['product.product'].sudo().search([('name','in', [x['name'] for x in payload['items']])]).mapped('name')
                        dbel_pr_name = [x['name'] for x in result_dobel_name]
                        duplicate_name = [x for x  in dbel_pr_name if dbel_pr_name.count(x)>1]
                        print("duplicate_name",duplicate_name)


                        sql = """SELECT default_code FROM product_product"""
                        request.env.cr.execute(sql,())
                        result_db_pr = request.env.cr.dictfetchall()
                        print("result_db_pr",result_db_pr)

                        db_pr_code = [x['default_code'] for x in result_db_pr]


                        db_pr = request.env['product.product'].sudo().search([])

                        # print("UOM",x['uom'])
                        # print("HAVE UOM",db_uom.filtered(lambda n:n.name==x['uom']))

                        # no_code_prods = [x for x in payload['items'] if x['name'] in [y['name']for y in db_pr.filtered(lambda z:z.default_code != x['code'] and z.uom_id.name == x['uom'])]]
                        # no_name_prods = [x for x in payload['items'] if x['code'] in [y['default_code'] for y in db_pr.filtered(lambda z:z.name != x['name'] and z.uom_id.name == x['uom'])]]
                        # no_uom_prods = [x for x in payload['items'] if x['code'] in [y['default_code'] for y in db_pr.filtered(lambda z:z.name == x['name'] and z.uom_id.name != x['uom'])]]
                        # no_name_uom_prods = [x for x in payload['items'] if x['code'] in [y['default_code'] for y in db_pr.filtered(lambda z:z.name != x['name'] and z.uom_id.name != x['uom'])]]
                        
                        # no_code_prodo = [{'code':x['default_code'],'name':x['name'],'uom':x['uom_id']['name']}for x in db_pr.filtered(lambda n:n.name in [z['name'] for z in no_code_prods])]
                        # no_name_prodo = [{'code':x['default_code'],'name':x['name'],'uom':x['uom_id']['name']}for x in db_pr.filtered(lambda n:n.default_code in [z['code'] for z in no_name_prods])]
                        # no_uom_prodo = [{'code':x['default_code'],'name':x['name'],'uom':x['uom_id']['name']}for x in db_pr.filtered(lambda n:n.default_code in [z['code'] for z in no_uom_prods])]
                        # no_name_uom_prodo = [{'code':x['default_code'],'name':x['name'],'uom':x['uom_id']['name']}for x in db_pr.filtered(lambda n:n.default_code in [z['code'] for z in no_name_uom_prods])]

                        # in_no_validate_prods = [
                        # {
                        # 'code':x['code'],
                        # 'name':x['name'],
                        # 'uom':x['uom'],
                        # 'status':-99,
                        # 'message':'code and name not matched',
                        # 'odoo':[{
                        # 'code':x['default_code'],
                        # 'name':x['name'],
                        # 'uom':x['uom_id']['name']}
                        # for x in db_pr.filtered(lambda n:n.name==x['name'])]}
                        # for x in payload['items'] if x['code'] not in db_pr.mapped('default_code')
                        # and x['name'] not in db_pr.mapped('name')
                        # and x['code'] not in duplicate_code]

                        in_validate_uom_prods = [
                        {
                        'code':x['code'],
                        'name':x['name'],
                        'uom':x['uom'],
                        'status':'00',
                        'index':x['index'],
                        'message':'uom matched',
                        'odoo':[{
                        'code':x['code'],
                        'name':x['name'],
                        'uom':x['uom']}]}
                        # for x in payload['items'] if x['uom'].lower() in [x.lower() for x in db_uom.mapped('name')]
                        for x in payload['items'] if x['uom'].lower() in [x.lower() for x in db_uom]
                        # for x in payload['items'] if x['uom'].lower() in db_uom.mapped('name'.lower())
                        and not x['code']]


                        not_uom_prods = [
                        {
                        'code':x['code'],
                        'name':x['name'],
                        'uom':x['uom'],
                        'status':-99,
                        'index':x['index'],
                        'message':'uom not match',
                        'odoo':False}
                        # for x in payload['items'] if x['uom'].lower() not in [x.lower() for x in db_uom.mapped('name')]
                        for x in payload['items'] if x['uom'].lower() not in [x.lower() for x in db_uom]
                        # for x in payload['items'] if x['uom'].lower() not in db_uom.mapped('name'.lower())
                        and not x['code']]

                        in_no_validate_prods = [
                        {
                        'code':x['code'],
                        'name':x['name'],
                        'uom':x['uom'],
                        'status':-99,
                        'index':x['index'],
                        'message':'code not found',
                        'odoo':False}
                        for x in payload['items'] if x['code'] not in db_pr_code
                        and x['code'] not in duplicate_code and x['code']]

                        in_validate_prods = [
                        {
                        'code':x['code'],
                        'name':x['name'],
                        'uom':x['uom'],
                        'status':'00',
                        'index':x['index'],
                        'message':'code matched',
                        'odoo':[{
                        'code':x['default_code'],
                        'name':x['name'],
                        'uom':x['uom_id']['name']}

                        for x in db_pr.filtered(lambda n:n.default_code==x['code'])]}
                        for x in payload['items'] if x['code'] in [y['default_code']
                        for y in db_pr.filtered(lambda z:z.default_code == x['code'] and "".join(z.name.lower().split()) == "".join(x['name'].lower().split()) and z.uom_id.name.lower() == x['uom'].lower() if x['uom'] else z.uom_id.name.lower() == x['uom'] and z.default_code == x['code'] and "".join(z.name.lower().split()) == "".join(x['name'].lower().split()))]
                        and x['code'] not in duplicate_code]

                        in_double_prods = [
                        {
                        'code':x['code'],
                        'name':x['name'],
                        'uom':x['uom'],
                        'status':-99,
                        'index':x['index'],
                        'message':'code is double',
                        'odoo':[{
                        'code':o['default_code'],
                        'name':o['name'],
                        'uom':o['uom_id']['name']}
                        for o in db_pr.filtered(lambda n:n.default_code==x['code'])]}
                        for x in payload['items'] if x['code'] in duplicate_code]

                        # in_double_name_prods = [
                        # {
                        # 'code':x['code'],
                        # 'name':x['name'],
                        # 'uom':x['uom'],
                        # 'status':-99,
                        # 'message':'name is double',
                        # 'odoo':[{
                        # 'code':o['default_code'],
                        # 'name':o['name'],
                        # 'uom':o['uom_id']['name']}
                        # for o in db_pr.filtered(lambda n:n.name==x['name'])]}
                        # for x in payload['items'] if x['name'] in duplicate_name]

                        # no_code_prods = [
                        # {
                        # 'code':x['code'],
                        # 'name':x['name'],
                        # 'uom':x['uom'],
                        # 'status':-99,
                        # 'message':'code not match',
                        # 'odoo':[{
                        # 'code':x['default_code'],
                        # 'name':x['name'],
                        # 'uom':x['uom_id']['name']}
                        # for x in db_pr.filtered(lambda n:n.name==x['name'])]}
                        # for x in payload['items'] if x['name'] in [y['name']
                        # for y in db_pr.filtered(lambda z:z.default_code != x['code'] and z.uom_id.name == x['uom'])]
                        # and x['code'] not in duplicate_code]

                        # no_code_uom_prods = [
                        # {
                        # 'code':x['code'],
                        # 'name':x['name'],
                        # 'uom':x['uom'],
                        # 'status':-99,
                        # 'message':'code and uom not match',
                        # 'odoo':[{
                        # 'code':x['default_code'],
                        # 'name':x['name'],
                        # 'uom':x['uom_id']['name']}
                        # for x in db_pr.filtered(lambda n:n.name==x['name'])]}
                        # for x in payload['items'] if x['name'] in [y['name']
                        # for y in db_pr.filtered(lambda z:z.default_code != x['code'] and z.uom_id.name != x['uom'])]
                        # and x['code'] not in duplicate_code]
                        # print("no_code_prods",no_code_prods)

                        # no_code_uom_prods = [
                        # {
                        # 'code':x['code'],
                        # 'name':x['name'],
                        # 'uom':x['uom'],
                        # 'status':-99,
                        # 'message':'code not found',
                        # 'odoo': False}
                        # for x in payload['items'] if x['name'] in [y['name']
                        # for y in db_pr.filtered(lambda z:z.default_code != x['code'] and z.uom_id.name != x['uom'])]
                        # and x['code'] not in duplicate_code]

                        no_name_prods = [
                        {
                        'code':x['code'],
                        'name':x['name'],
                        'uom':x['uom'],
                        'status':-99,
                        'index':x['index'],
                        'message':'name not match',
                        'odoo':[{
                        'code':x['default_code'],
                        'name':x['name'],
                        'uom':x['uom_id']['name']}
                        for x in db_pr.filtered(lambda n:n.default_code==x['code'])]}
                        for x in payload['items'] if x['code'] in [y.default_code
                        for y in db_pr.filtered(lambda z:"".join(z.name.lower().split()) != "".join(x['name'].lower().split()) and z.uom_id.name.lower() == x['uom'].lower() if x['uom'] else z.uom_id.name.lower() != x['uom'] and "".join(z.name.lower().split()) != "".join(x['name'].lower().split()))]
                        and x['code'] not in duplicate_code]

                        no_uom_prods = [
                        {
                        'code':x['code'],
                        'name':x['name'],
                        'uom':x['uom'],
                        'status':-99,
                        'index':x['index'],
                        'message':'uom not match',
                        'odoo':[{
                        'code':x['default_code'],
                        'name':x['name'],
                        'uom':x['uom_id']['name']}
                        for x in db_pr.filtered(lambda n:n.default_code==x['code'])]}
                        for x in payload['items'] if x['code'] in [y['default_code']
                        for y in db_pr.filtered(lambda z:"".join(z.name.lower().split()) == "".join(x['name'].lower().split()) and z.uom_id.name.lower() != x['uom'].lower() if x['uom'] else z.uom_id.name.lower() != x['uom'] and "".join(z.name.lower().split()) == "".join(x['name'].lower().split()))]
                        and x['code'] not in duplicate_code]

                        no_name_uom_prods = [
                        {
                        'code':x['code'],
                        'name':x['name'],
                        'uom':x['uom'],
                        'status':-99,
                        'index':x['index'],
                        'message':'name and uom not match',
                        'odoo':[{
                        'code':x['default_code'],
                        'name':x['name'],
                        'uom':x['uom_id']['name']}
                        for x in db_pr.filtered(lambda n:n.default_code==x['code'])]}
                        for x in payload['items'] if x['code'] in [y['default_code']
                        for y in db_pr.filtered(lambda z:"".join(z.name.lower().split()) != "".join(x['name'].lower().split()) and z.uom_id.name.lower() != x['uom'].lower() if x['uom'] else z.uom_id.name.lower() != x['uom'] and "".join(z.name.lower().split()) != "".join(x['name'].lower().split()))]
                        and x['code'] not in duplicate_code]
                        response={
                        'status_code':'00',
                        'status_msg':"Get data success..",
                        'data': [{
                        "eSanqua": in_no_validate_prods+in_validate_prods+in_double_prods+no_name_prods+no_uom_prods+no_name_uom_prods+not_uom_prods+in_validate_uom_prods
                        }]
                        }

                        # response={
                        # 'status_code':'00',
                        # 'status_msg':"Get data success..",
                        # 'data': [{
                        # "eSanqua": in_validate_uom_prods+not_uom_prods
                        # }]
                        # }

                    return response
            except Exception as e:
                request.env.cr.rollback()
                respond={'status_code':-99,'status_msg':e}
        elif not validates:
            respond={'status_code':-99,'status_msg':'Mandatory field was empty!'}

        return respond

    # @http.route("/api/cek_produk", type="json",auth='none', methods=["POST"], csrf=False)
    # def cek_produk(self, **payload):
        
    #     request._json_response = alternative_json_response.__get__(request, JsonRequest)
    #     # db="SANQUA_LIVE_16032022"
    #     db_name = request.env['ir.config_parameter'].sudo().search([('key','=','api_db_name')])
    #     usr_login = request.env['ir.config_parameter'].sudo().search([('key','=','api_login_name')])
    #     usr_pass = request.env['ir.config_parameter'].sudo().search([('key','=','api_login_pass')])
    #     db=db_name.value
    #     login=usr_login.value
    #     password=usr_pass.value
    #     request.session.authenticate(db,login,password)
    #     payload = json.loads(request.httprequest.data)
    #     items = (payload.get("items"))
    #     validates = all([items])
    #     if payload and validates:
    #         try:
    #             for x in payload['items']:
    #                 product_obj = request.env['product.product'].sudo().search([('default_code','=', x['code']),('name','=', x['name']),('uom_id.name','=', x['uom'])])
    #                 if payload:
    #                     dbel_pr_code = request.env['product.product'].sudo().search([('default_code','in', [x['code'] for x in payload['items']])]).mapped('default_code')
    #                     duplicate_code = [x for x  in dbel_pr_code if dbel_pr_code.count(x)>1]
    #                     dbel_pr_name = request.env['product.product'].sudo().search([('name','in', [x['name'] for x in payload['items']])]).mapped('name')
    #                     duplicate_name = [x for x  in dbel_pr_name if dbel_pr_name.count(x)>1]
    #                     db_pr = request.env['product.product'].sudo().search([])

    #                     # no_code_prods = [x for x in payload['items'] if x['name'] in [y['name']for y in db_pr.filtered(lambda z:z.default_code != x['code'] and z.uom_id.name == x['uom'])]]
    #                     # no_name_prods = [x for x in payload['items'] if x['code'] in [y['default_code'] for y in db_pr.filtered(lambda z:z.name != x['name'] and z.uom_id.name == x['uom'])]]
    #                     # no_uom_prods = [x for x in payload['items'] if x['code'] in [y['default_code'] for y in db_pr.filtered(lambda z:z.name == x['name'] and z.uom_id.name != x['uom'])]]
    #                     # no_name_uom_prods = [x for x in payload['items'] if x['code'] in [y['default_code'] for y in db_pr.filtered(lambda z:z.name != x['name'] and z.uom_id.name != x['uom'])]]
                        
    #                     # no_code_prodo = [{'code':x['default_code'],'name':x['name'],'uom':x['uom_id']['name']}for x in db_pr.filtered(lambda n:n.name in [z['name'] for z in no_code_prods])]
    #                     # no_name_prodo = [{'code':x['default_code'],'name':x['name'],'uom':x['uom_id']['name']}for x in db_pr.filtered(lambda n:n.default_code in [z['code'] for z in no_name_prods])]
    #                     # no_uom_prodo = [{'code':x['default_code'],'name':x['name'],'uom':x['uom_id']['name']}for x in db_pr.filtered(lambda n:n.default_code in [z['code'] for z in no_uom_prods])]
    #                     # no_name_uom_prodo = [{'code':x['default_code'],'name':x['name'],'uom':x['uom_id']['name']}for x in db_pr.filtered(lambda n:n.default_code in [z['code'] for z in no_name_uom_prods])]

    #                     # in_no_validate_prods = [
    #                     # {
    #                     # 'code':x['code'],
    #                     # 'name':x['name'],
    #                     # 'uom':x['uom'],
    #                     # 'status':-99,
    #                     # 'message':'code and name not matched',
    #                     # 'odoo':[{
    #                     # 'code':x['default_code'],
    #                     # 'name':x['name'],
    #                     # 'uom':x['uom_id']['name']}
    #                     # for x in db_pr.filtered(lambda n:n.name==x['name'])]}
    #                     # for x in payload['items'] if x['code'] not in db_pr.mapped('default_code')
    #                     # and x['name'] not in db_pr.mapped('name')
    #                     # and x['code'] not in duplicate_code]

    #                     in_no_validate_prods = [
    #                     {
    #                     'code':x['code'],
    #                     'name':x['name'],
    #                     'uom':x['uom'],
    #                     'status':-99,
    #                     'message':'code not found',
    #                     'odoo':False}
    #                     for x in payload['items'] if x['code'] not in db_pr.mapped('default_code')
    #                     and x['code'] not in duplicate_code]

    #                     in_validate_prods = [
    #                     {
    #                     'code':x['code'],
    #                     'name':x['name'],
    #                     'uom':x['uom'],
    #                     'status':'00',
    #                     'message':'code matched',
    #                     'odoo':[{
    #                     'code':x['default_code'],
    #                     'name':x['name'],
    #                     'uom':x['uom_id']['name']}
    #                     for x in db_pr.filtered(lambda n:n.default_code==x['code'])]}
    #                     for x in payload['items'] if x['code'] in [y['default_code']
    #                     for y in db_pr.filtered(lambda z:z.default_code == x['code'] and z.name.lower() == x['name'].lower() and z.uom_id.name.lower() == x['uom'].lower() if x['uom'] else z.uom_id.name.lower() == x['uom'] and z.default_code == x['code'] and z.name.lower() == x['name'].lower())]
    #                     and x['code'] not in duplicate_code]

    #                     in_double_prods = [
    #                     {
    #                     'code':x['code'],
    #                     'name':x['name'],
    #                     'uom':x['uom'],
    #                     'status':-99,
    #                     'message':'code is double',
    #                     'odoo':[{
    #                     'code':o['default_code'],
    #                     'name':o['name'],
    #                     'uom':o['uom_id']['name']}
    #                     for o in db_pr.filtered(lambda n:n.default_code==x['code'])]}
    #                     for x in payload['items'] if x['code'] in duplicate_code]

    #                     # in_double_name_prods = [
    #                     # {
    #                     # 'code':x['code'],
    #                     # 'name':x['name'],
    #                     # 'uom':x['uom'],
    #                     # 'status':-99,
    #                     # 'message':'name is double',
    #                     # 'odoo':[{
    #                     # 'code':o['default_code'],
    #                     # 'name':o['name'],
    #                     # 'uom':o['uom_id']['name']}
    #                     # for o in db_pr.filtered(lambda n:n.name==x['name'])]}
    #                     # for x in payload['items'] if x['name'] in duplicate_name]

    #                     # no_code_prods = [
    #                     # {
    #                     # 'code':x['code'],
    #                     # 'name':x['name'],
    #                     # 'uom':x['uom'],
    #                     # 'status':-99,
    #                     # 'message':'code not match',
    #                     # 'odoo':[{
    #                     # 'code':x['default_code'],
    #                     # 'name':x['name'],
    #                     # 'uom':x['uom_id']['name']}
    #                     # for x in db_pr.filtered(lambda n:n.name==x['name'])]}
    #                     # for x in payload['items'] if x['name'] in [y['name']
    #                     # for y in db_pr.filtered(lambda z:z.default_code != x['code'] and z.uom_id.name == x['uom'])]
    #                     # and x['code'] not in duplicate_code]

    #                     # no_code_uom_prods = [
    #                     # {
    #                     # 'code':x['code'],
    #                     # 'name':x['name'],
    #                     # 'uom':x['uom'],
    #                     # 'status':-99,
    #                     # 'message':'code and uom not match',
    #                     # 'odoo':[{
    #                     # 'code':x['default_code'],
    #                     # 'name':x['name'],
    #                     # 'uom':x['uom_id']['name']}
    #                     # for x in db_pr.filtered(lambda n:n.name==x['name'])]}
    #                     # for x in payload['items'] if x['name'] in [y['name']
    #                     # for y in db_pr.filtered(lambda z:z.default_code != x['code'] and z.uom_id.name != x['uom'])]
    #                     # and x['code'] not in duplicate_code]
    #                     # print("no_code_prods",no_code_prods)

    #                     # no_code_uom_prods = [
    #                     # {
    #                     # 'code':x['code'],
    #                     # 'name':x['name'],
    #                     # 'uom':x['uom'],
    #                     # 'status':-99,
    #                     # 'message':'code not found',
    #                     # 'odoo': False}
    #                     # for x in payload['items'] if x['name'] in [y['name']
    #                     # for y in db_pr.filtered(lambda z:z.default_code != x['code'] and z.uom_id.name != x['uom'])]
    #                     # and x['code'] not in duplicate_code]

    #                     no_name_prods = [
    #                     {
    #                     'code':x['code'],
    #                     'name':x['name'],
    #                     'uom':x['uom'],
    #                     'status':-99,
    #                     'message':'name not match',
    #                     'odoo':[{
    #                     'code':x['default_code'],
    #                     'name':x['name'],
    #                     'uom':x['uom_id']['name']}
    #                     for x in db_pr.filtered(lambda n:n.default_code==x['code'])]}
    #                     for x in payload['items'] if x['code'] in [y.default_code
    #                     for y in db_pr.filtered(lambda z:z.name.lower() != x['name'].lower() and z.uom_id.name.lower() == x['uom'].lower() if x['uom'] else z.uom_id.name.lower() != x['uom'] and z.name.lower() != x['name'].lower())]
    #                     and x['code'] not in duplicate_code]

    #                     no_uom_prods = [
    #                     {
    #                     'code':x['code'],
    #                     'name':x['name'],
    #                     'uom':x['uom'],
    #                     'status':-99,
    #                     'message':'uom not match',
    #                     'odoo':[{
    #                     'code':x['default_code'],
    #                     'name':x['name'],
    #                     'uom':x['uom_id']['name']}
    #                     for x in db_pr.filtered(lambda n:n.default_code==x['code'])]}
    #                     for x in payload['items'] if x['code'] in [y['default_code']
    #                     for y in db_pr.filtered(lambda z:z.name.lower() == x['name'].lower() and z.uom_id.name.lower() != x['uom'].lower() if x['uom'] else z.uom_id.name.lower() != x['uom'] and z.name.lower() == x['name'].lower())]
    #                     and x['code'] not in duplicate_code]

    #                     no_name_uom_prods = [
    #                     {
    #                     'code':x['code'],
    #                     'name':x['name'],
    #                     'uom':x['uom'],
    #                     'status':-99,
    #                     'message':'name and uom not match',
    #                     'odoo':[{
    #                     'code':x['default_code'],
    #                     'name':x['name'],
    #                     'uom':x['uom_id']['name']}
    #                     for x in db_pr.filtered(lambda n:n.default_code==x['code'])]}
    #                     for x in payload['items'] if x['code'] in [y['default_code']
    #                     for y in db_pr.filtered(lambda z:z.name.lower() != x['name'].lower() and z.uom_id.name.lower() != x['uom'].lower() if x['uom'] else z.uom_id.name.lower() != x['uom'] and z.name.lower() != x['name'].lower())]
    #                     and x['code'] not in duplicate_code]
    #                     response={
    #                     'status_code':'00',
    #                     'status_msg':"Get data success..",
    #                     'data': [{
    #                     "eSanqua": in_no_validate_prods+in_validate_prods+in_double_prods+no_name_prods+no_uom_prods+no_name_uom_prods
    #                     }]
    #                     }
    #                 return response
    #         except Exception as e:
    #             request.env.cr.rollback()
    #             respond={'status_code':-99,'status_msg':e}
    #     elif not validates:
    #         respond={'status_code':-99,'status_msg':'Mandatory field was empty!'}

    #     return respond

class PurchaseRequestAPI(models.Model):
    _inherit = 'purchase.request'

    def send_stat(self,const):
        # print("CONS SEND STAT", const)
        # print("THIS PR NUMBER", self.name)
        this_state = 0
        if const[0] == 'approved':
            this_state = 2
        elif const[0] == 'close':
            this_state = 4
        elif const[0] == 'cancel':
            this_state = 5
        elif const[0] == 'rejected':
            this_state = -1
        elif const == [False]:
            this_state = 0
        mis_api = request.env['ir.config_parameter'].sudo().search([('key','=','api_update_pr')])
        url = mis_api.value
        payload = json.dumps({
            "pr_no": self.name,
            "status": this_state
            })
        headers = {'Content-Type': 'application/json'}
        response = requests.request("POST", url, headers=headers, data=payload)
        print(response.text)

    def write(self,vals):
        svals = 'status_pr' in vals
        stvals = 'state' in vals
        cons = []
        if svals:
            previous_state = self.status_pr
            new_state = vals.get('status_pr')
            # print("previous_state",previous_state)
            # print("new_state",new_state)
            if new_state != previous_state:
                cons.append(new_state)
                if cons[0] == 'open' and self.state == 'approved':
                    cons = self.state
        if stvals:
            previous_state = self.state
            new_state = vals.get('state')
            # print("previous_state",previous_state)
            # print("new_state",new_state)
            if new_state != previous_state and new_state in ['approved','rejected']:
                cons.append(new_state)
        if cons:
        # if cons and cons != [False]:
            try:
                self.send_stat(const=cons)
            except requests.exceptions.ConnectionError as e:
                print("Lost connection...")
        result = super(PurchaseRequestAPI, self).write(vals)
        return result

class PurchaseOrderAPI(models.Model):
    _inherit = 'purchase.order'

    def send_item(self,const):
        mis_api = request.env['ir.config_parameter'].sudo().search([('key','=','api_create_po')])
        url = mis_api.value
        payload = json.dumps({
            "vendor": {
                "code": self.partner_id.code,
                "name": self.partner_id.name
            },
            "company": {
                "code_plant": self.company_id.code_plant,
                "name": self.company_id.name
            },
            # "product": [{
            #     "code": "",
            #     "name": "",
            #     "uom": {
            #         "id": "",
            #         "name": ""
            #         },
            #     "currency": {
            #         "id": "",
            #         "name": ""
            #         },
            #     "price_unit": 0,
            #     "created_at": "YYYY-MM-DD HH:mm:ss"}]
            "product":const
            })
        headers = {'Content-Type': 'application/json'}
        response = requests.request("POST", url, headers=headers, data=payload)
        print(response.text)

    def write(self,vals):
        spovals = 'state' in vals
        cons = []
        if spovals:
            previous_state = self.state
            new_state = vals.get('state')
            print("previous_state",previous_state)
            print("new_state",new_state)
            self.env.context = dict(self.env.context)
            self.env.context.update({'time': datetime.strftime(fields.Datetime.context_timestamp(self, datetime.now()), "%Y-%m-%d %H:%M:%S")})
            crntime = self.env.context.get('time')
            if new_state != previous_state and new_state=='purchase':
                for x in self.order_line:
                    cons.append({
                        "code":x.product_id.default_code,
                        "name":x.name,
                        "uom":{
                            "id":x.product_uom.id,
                            "name":x.product_uom.name
                            },
                        "currency":{
                            "id":self.currency_id.id,
                            "name":self.currency_id.name
                            },
                        "price_unit":x.price_unit,
                        "created_at":crntime
                        })
                # print("cons xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", cons)
                # print("cons time xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", self.env.context.get('time'))
            if cons:
                try:
                    self.send_item(const=cons)
                except requests.exceptions.ConnectionError as e:
                    print("Lost connection...")
        result = super(PurchaseOrderAPI, self).write(vals)
        return result