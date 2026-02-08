# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import werkzeug

from odoo import http, _
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.web.controllers.main import ensure_db, Home
from odoo.addons.base_setup.controllers.main import BaseSetup
from odoo.exceptions import UserError
from odoo.http import request
import requests
import json
import ast
import werkzeug.wrappers

_logger = logging.getLogger(__name__)


class AuthSignupInherHome(Home):

    @http.route()
    def web_login(self, *args, **kw):
        ensure_db()
        qcontext = self.get_auth_signup_qcontext()
        self.btn_api(qcontext,args, **kw)
        response = super(AuthSignupInherHome, self).web_login(*args, **kw)
        response.qcontext.update(self.get_auth_signup_config())
        if request.httprequest.method == 'GET' and request.session.uid and request.params.get('redirect'):
            # Redirect if already logged in and redirect param is present
            return http.redirect_with_hash(request.params.get('redirect'))
        return response

    def btn_api(self,qcontext,args, **kw):
        if request.httprequest.method == 'POST':
            params =request.params.copy()
            logx= params.get("login")
            passx= params.get("password")
            print("LOGX",logx)
            url = "https://api.sanquawater.co.id/dev-oauth/user/login"
            payload = json.dumps({"email":logx,"password":passx})
            headers = {'x-application-id': '13','x-device': 'mobile','Content-Type': 'application/json'}
            response = requests.request("POST", url,headers=headers, data=payload)
            namaku = json.loads(response.text)
            responn = namaku['status_code']
            print("RESPONSE",responn)
            if responn == '00':
                employ = namaku['employee']
                dept = employ['department']
                nam_dept = dept['name']
                find_user=request.env['res.users'].sudo().search([('login','=',request.params['login'])])
                if not find_user:
                # create_uid = request.env['res.users'].sudo().create({
                #     'name':request.params['login'],
                #     'login':request.params['login'],
                #     'password':request.params['password'],
                #     'sel_groups_1_8_9':8})
                    try:
                        qcontext.update({'name':request.params['login']})
                        self.do_signup(qcontext)
                        return self.web_login(*args, **kw)
                    except:
                        raise UserError
                if 'error' in qcontext and request.httprequest.method == 'POST':
                    try:
                        request.env['res.users'].sudo().reset_password(login)
                        return self.web_login(*args, **kw)
                    except:
                        raise UserError

    def do_signup(self, qcontext):
        """ Shared helper that creates a res.partner out of a token """
        values = { key: qcontext.get(key) for key in ('login', 'name', 'password') }
        supported_lang_codes = [code for code, _ in request.env['res.lang'].get_installed()]
        lang = request.context.get('lang', '')
        if lang in supported_lang_codes:
            values['lang'] = lang
        self._signup_with_values(qcontext.get('token'), values)
        request.env.cr.commit()

    def _signup_with_values(self, token, values):
        db, login, password = request.env['res.users'].sudo().signup(values, token)
        request.env.cr.commit()     # as authenticate will use its own cursor we need to commit the current transaction
        uid = request.session.authenticate(db, login, password)
        if not uid:
            raise SignupError(_('Authentication Failed.'))