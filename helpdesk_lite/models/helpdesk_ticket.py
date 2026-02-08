# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, SUPERUSER_ID, _
import re
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from odoo.http import request
import requests
import json
import logging
import pytz
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import time

AVAILABLE_PRIORITIES = [
    ('0', 'Low'),
    ('1', 'Normal'),
    ('2', 'High'),
    ('3', 'Urgent'),
]

_logger = logging.getLogger(__name__)


class HelpdeskTicket(models.Model):
    _name = "helpdesk_lite.ticket"
    _description = "Helpdesk Tickets"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = "priority desc, create_date desc"
    _mail_post_access = 'read'

    @api.model
    def _get_default_stage_id(self):
        return self.env['helpdesk_lite.stage'].search([], order='sequence', limit=1)

    def domain_user(self):
        dom_user = self.env.ref('base.group_user').users.ids
        return [('id', 'in', dom_user)]

    name = fields.Char(string='Subject', track_visibility='always', required=True)
    description = fields.Text('Description')
    explain = fields.Text('Detail Perbaikan')
    partner_id = fields.Many2one('res.partner', string='Customer', track_visibility='onchange', index=True)
    commercial_partner_id = fields.Many2one(
        related='partner_id.commercial_partner_id', string='Customer Company', store=True, index=True)
    contact_name = fields.Char('Contact Name')
    email_from = fields.Char('Email', help="Email address of the contact", index=True)
    user_id = fields.Many2one('res.users', string='Assigned to', track_visibility='onchange', index=True, default=False, domain=domain_user)
    team_id = fields.Many2one('helpdesk_lite.team', string='Support Team', track_visibility='onchange',
        default=lambda self: self.env['helpdesk_lite.team'].sudo()._get_default_team_id(user_id=self.env.uid),
        index=True, help='When sending mails, the default email address is taken from the support team.')
    date_deadline = fields.Datetime(string='Deadline', track_visibility='onchange')
    date_done = fields.Datetime(string='Done', track_visibility='onchange')

    stage_id = fields.Many2one('helpdesk_lite.stage', string='Stage', index=True, track_visibility='onchange',
                               domain="[]",
                               copy=False,
                               group_expand='_read_group_stage_ids',
                               default=_get_default_stage_id)
    priority = fields.Selection(AVAILABLE_PRIORITIES, 'Priority', index=True, default='1', track_visibility='onchange')
    kanban_state = fields.Selection([('normal', 'Normal'), ('blocked', 'Blocked'), ('done', 'Ready for next stage')],
                                    string='Kanban State', track_visibility='onchange',
                                    required=True, default='normal',
                                    help="""A Ticket's kanban state indicates special situations affecting it:\n
                                           * Normal is the default situation\n
                                           * Blocked indicates something is preventing the progress of this ticket\n
                                           * Ready for next stage indicates the ticket is ready to go to next stage""")

    color = fields.Integer('Color Index')
    legend_blocked = fields.Char(related="stage_id.legend_blocked", readonly=True)
    legend_done = fields.Char(related="stage_id.legend_done", readonly=True)
    legend_normal = fields.Char(related="stage_id.legend_normal", readonly=True)

    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id,track_visibility='onchange')
    start_date = fields.Datetime(string='Start Date', track_visibility='onchange')
    code = fields.Char('No.Tiket',default='/',track_visibility='onchange')
    category_id = fields.Many2one('helpdesk_lite.category',track_visibility='onchange')
    sub_category_id = fields.Many2one('helpdesk_lite.sub.category',track_visibility='onchange')
    cek_mgr = fields.Boolean(compute='cek_akses')
    cek_assign = fields.Boolean(compute='cek_akses')
    user_create = fields.Many2one('res.users')
    department = fields.Char(track_visibility='onchange')
    subject_id = fields.Many2one('helpdesk_lite.subject',track_visibility='onchange')    

    @api.depends('name')
    def cek_akses(self):
        for rec in self:
            my_user = self.env.uid
            dom_user = self.env.ref('helpdesk_lite.group_helpdesk_lite_manager').users.ids
            if my_user in dom_user:
                rec.cek_mgr = True
            else:
                rec.cek_mgr = False
            if not rec.user_create:
                self.user_create = self._context.get('uid')
            if self._context.get('uid') == self.user_id.id or rec.cek_mgr:
                rec.cek_assign = True
            elif not self.user_id:
                rec.cek_assign = True
            else:
                rec.cek_assign = False

    @api.onchange('create_date')
    def _onchange_create_date(self):
        for rec in self:
            if rec.create_date:
                self.env.cr.execute("""UPDATE helpdesk_lite_ticket SET create_date=%s 
                    WHERE id="""+str(int(self._origin.id))+"""""",(rec.create_date,))
            else:
                rec.create_date = rec.create_date


    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """ This function sets partner email address based on partner
        """
        res_user = self.env['res.users'].search([('partner_id','=',self.partner_id.id)])
        self.email_from = self.partner_id.email
        self.company_id = res_user.company_id.id
        self.department = res_user.department


    @api.onchange('subject_id')
    def _onchange_subject_id(self):
        self.name = self.subject_id.name


    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        if self.stage_id:
            if not self.user_id and self.cek_mgr == False:
                raise ValidationError(_("Check assigned before"))

    def copy(self, default=None):
        if default is None:
            default = {}
        default.update(name=_('%s (copy)') % (self.name))
        return super(HelpdeskTicket, self).copy(default=default)

    # def _can_add__recipient(self, partner_id):
    #     if not self.partner_id.email:
    #         return False
    #     if self.partner_id in self.message_follower_ids.mapped('partner_id'):
    #         return False
    #     return True

    # def message_get_suggested_recipients(self):
    #     recipients = super(HelpdeskTicket, self).message_get_suggested_recipients()
    #     try:
    #         for tic in self:
    #             if tic.partner_id:
    #                 if tic._can_add__recipient(tic.partner_id):
    #                     tic._message_add_suggested_recipient(recipients, partner=tic.partner_id,
    #                                                          reason=_('Customer'))
    #             elif tic.email_from:
    #                 tic._message_add_suggested_recipient(recipients, email=tic.email_from,
    #                                                      reason=_('Customer Email'))
    #     except AccessError:  # no read access rights -> just ignore suggested recipients because this imply modifying followers
    #         pass
    #     return recipients

    # def _email_parse(self, email):
    #     match = re.match(r"(.*) *<(.*)>", email)
    #     if match:
    #         contact_name, email_from =  match.group(1,2)
    #     else:
    #         match = re.match(r"(.*)@.*", email)
    #         contact_name =  match.group(1)
    #         email_from = email
    #     return contact_name, email_from

    # @api.model
    # def message_new(self, msg, custom_values=None):
    #     match = re.match(r"(.*) *<(.*)>", msg.get('from'))
    #     if match:
    #         contact_name, email_from =  match.group(1,2)
    #     else:
    #         match = re.match(r"(.*)@.*", msg.get('from'))
    #         contact_name =  match.group(1)
    #         email_from = msg.get('from')

    #     body = tools.html2plaintext(msg.get('body'))
    #     bre = re.match(r"(.*)^-- *$", body, re.MULTILINE|re.DOTALL|re.UNICODE)
    #     desc = bre.group(1) if bre else None

    #     defaults = {
    #         'name':  msg.get('subject') or _("No Subject"),
    #         'email_from': email_from,
    #         'description':  desc or body,
    #     }

    #     partner = self.env['res.partner'].sudo().search([('email', '=ilike', email_from)], limit=1)
    #     if partner:
    #         defaults.update({
    #             'partner_id': partner.id,
    #         })
    #     else:
    #         defaults.update({
    #             'contact_name': contact_name,
    #         })

    #     create_context = dict(self.env.context or {})
    #     # create_context['default_user_id'] = False
    #     # create_context.update({
    #     #     'mail_create_nolog': True,
    #     # })

    #     company_id = False
    #     if custom_values:
    #         defaults.update(custom_values)
    #         team_id = custom_values.get('team_id')
    #         if team_id:
    #             team = self.env['helpdesk_lite.team'].sudo().browse(team_id)
    #             if team.company_id:
    #                 company_id = team.company_id.id
    #     if not company_id and partner.company_id:
    #         company_id = partner.company_id.id
    #     defaults.update({'company_id': company_id})

    #     return super(HelpdeskTicket, self.with_context(create_context)).message_new(msg, custom_values=defaults)

    @api.model_create_single
    def create(self, vals):
        # context = dict(self.env.context)
        # context.update({
        #     'mail_create_nosubscribe': False,
        # })
        # res = super(HelpdeskTicket, self.with_context(context)).create(vals)
        res = super(HelpdeskTicket, self).create(vals)
        # res = super().create(vals)
        # print("NAMA", res.name)
        sql = """SELECT id AS id,name AS name FROM helpdesk_lite_subject WHERE name ILIKE '{}' GROUP BY id,name"""
        request.cr.execute(sql.format(str(res.name,)))
        result = request.cr.dictfetchall()
        if result:
            s_id = result[0]['id']
            s_name = result[0]['name']
            # print("result",s_id)
            res.subject_id = s_id
            # print("result", result[1])
        else:
            # print("GAK ADA DATA")
            fin_s = self.env['helpdesk_lite.subject'].sudo().create({'name':res.name})
            res.subject_id = fin_s.id
        send = 0
        if res.name:
            # res.create_date = datetime.strptime(str(res.create_date), "%d %B, %Y %H:%M")
            res_user = self.env['res.users'].search([('id','=',self._context.get('uid'))])
            res_part = self.env['res.users'].search([('partner_id','=',res.partner_id.id)])
            res.update({'user_create': res_user.id})
            res.update({'email_from': res_user.login})
            res.update({'department': res_user.department or res_part.department})
            res.update({'company_id': res_user.company_id})
            res.update({'email_from': res_part.login})
            res.update({'start_date': res.create_date})
            vals.update({'partner_id': res.partner_id.id})
            # self.env.cr.execute("""UPDATE helpdesk_lite_ticket SET create_date=%s 
            #     WHERE id="""+str(int(res.id))+"""""",(res.start_date,))
        # if res.partner_id:
        #     res.message_subscribe([res.partner_id.id])
        if res.sub_category_id:
            sequence =  self.env['ir.sequence'].next_by_code(res.sub_category_id.sequence_id.code)
            res.update({'code': sequence})
            vals.update({
                'code': sequence
                })
        # if res.partner_id:
        #     res.action_send_email()
        # res.send_telegram(vals)
        return res

    def delete_mail(self):
        for rec in self:
            rec.env['mail.message'].sudo().search([('model','=','helpdesk_lite.ticket'),('res_id','=',rec.id)]).unlink()            

    def write(self, vals):
        # stage change: update date_last_stage_update
        # print("VALSS",vals)
        tracking = False
        svals = 'stage_id' in vals
        subvals = 'sub_category_id' in vals
        pvals = 'partner_id' in vals
        uvals = 'user_id' in vals
        if svals:
            previous_state = self.stage_id.id
            new_state = vals.get('stage_id')
            if new_state != previous_state and self.cek_assign == False:
                raise ValidationError(_("You are not allowed perform that move !"))
            if 'kanban_state' not in vals:
                vals['kanban_state'] = 'normal'
            stage = self.env['helpdesk_lite.stage'].browse(vals['stage_id'])
            if stage.last:
                vals.update({'date_done': fields.Datetime.now()})
            elif stage.id == 1:
                vals.update({
                    'user_id': False,
                    'start_date':False,
                    'date_done':False
                    })
            elif stage.id == 2:
                vals.update({
                    'start_date':fields.Datetime.now()
                    })
            else:
                vals.update({'date_done': False})
        res = super(HelpdeskTicket, self.with_context(tracking_disable=False)).write(vals)
        if subvals:
            sub_category = vals.get('sub_category_id')
            m_ct = self.env['helpdesk_lite.sub.category'].search([('id','=',sub_category)])
            sequence =  self.env['ir.sequence'].next_by_code(m_ct.sequence_id.code)
            vals.update({'code': sequence})
        # if pvals:
            # self.action_send_email()
        if uvals:
            # print("UVALLLLLLLLLLLLLLLLLLLL???????????")
            self.start_date = self.create_date
            # self.action_send_email_assigned(vals)
        if vals.get('stage_id') == 2:
            # print("STAGE 3")
            # self.action_send_email_assigned(vals)
            vals.update({
                'code':self.code,
                'name':self.name,
                'partner_id':self.partner_id.id,
                'department':self.department or '-'
                })
            # self.send_telegram(vals)
        if vals.get('stage_id') == 3:
            # print("STAGE 3")
            # self.action_send_email_solved(vals)
            vals.update({
                'code':self.code,
                'name':self.name,
                'partner_id':self.partner_id.id,
                'department':self.department or '-',
                'explain':self.explain or '-'
                })
            # self.send_telegram(vals)
        if vals.get('stage_id') == 4:
            # print("STAGE 4")
            # self.action_send_email_cancel(vals)
            vals.update({
                'code':self.code,
                'department':self.department or '-',
                'partner_id':self.partner_id.id,
                'name':self.name,
                'explain':self.explain or '-'
                })
            # self.send_telegram(vals)
        return res

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):

        search_domain = []

        # perform search
        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    def takeit(self):
        self.ensure_one()
        # print("tanggallllllll",self.create_date)
        self.start_date = fields.Datetime.now()
        # now= datetime.strftime(fields.Datetime.context_timestamp(self, datetime.now()), "%Y-%m-%d %H:%M:%S")
        # now = fields.datetime.now()
        # print("DATETETETETETE", now)
        # untuk Chat aja =========================================
        # self.message_post(body='xyz', message_type="comment", subtype_id=18, channel_ids=[6])
        # template_id = self.env['ir.model.data'].xmlid_to_res_id('helpdesk_lite.help_template_assign', raise_if_not_found=False)
        # self.message_post_with_template(template_id,partner_ids=[3],message_type="notification", subtype_id=18)
        vals = {
            'user_id' : self.env.uid,
            'code' : self.code,
            'partner_id' : self.partner_id.id,
            'department' : self.department,
            'email_from' : self.email_from,
            'stage_id' : 2
            # 'team_id': self.env['helpdesk_lite.team'].sudo()._get_default_team_id(user_id=self.env.uid).id
        }
        res = super(HelpdeskTicket, self.with_context(tracking_disable=True)).write(vals)
        if 'user_id' in vals:
            # print("TRUEE")
            vals.get('user_id')
            # self.action_send_email_assigned(vals)
            vals.update({'name':self.name})
        # self.send_telegram(vals)

        return res
        
    def _register_hook(self):
        HelpdeskTicket.website_form = bool(self.env['ir.module.module'].
                                           search([('name', '=', 'website_form'), ('state', '=', 'installed')]))
        if HelpdeskTicket.website_form:
            self.env['ir.model'].search([('model', '=', self._name)]).write({'website_form_access': True})
            self.env['ir.model.fields'].formbuilder_whitelist(
                self._name, ['name','description', 'category_id', 'sub_category_id' ,'date_deadline', 'priority', 'partner_id', 'user_id'])
        pass


    def action_send_email(self):
        # search the email template based on external id
        # print("APA JALAN EMAILNYA")
        template_id = self.env['ir.model.data'].xmlid_to_res_id('helpdesk_lite.help_template', raise_if_not_found=False)
        if template_id:
            for rec in self:
                rec.with_context(force_send=True,tracking_disable=True).message_post_with_template(template_id,email_layout_xmlid="helpdesk_lite.message_no_odoo_branding")


    def action_send_email_assigned(self,vals):
        template_id = self.env.ref('helpdesk_lite.help_template_assign').id
        template = self.env['mail.template'].browse(template_id)
        user_log = vals.get('user_id')
        to_user = self.env['res.users'].search([('id','=',user_log)]).login
        template.send_mail(self.id,email_values={
            'email_to': to_user,
            'email_cc': self.email_from}
            ,force_send=True)


    def action_send_email_solved(self,vals):
        template_id = self.env.ref('helpdesk_lite.help_template_solved').id
        template = self.env['mail.template'].browse(template_id)
        user_log = vals.get('user_id')
        to_user = self.env['res.users'].search([('id','=',user_log)]).login
        template.send_mail(self.id,email_values={
            'email_to': self.user_id.login,
            'email_cc': self.email_from}
            ,force_send=True)


    def action_send_email_cancel(self,vals):
        template_id = self.env.ref('helpdesk_lite.help_template_cancel').id
        template = self.env['mail.template'].browse(template_id)
        user_log = vals.get('user_id')
        to_user = self.env['res.users'].search([('id','=',user_log)]).login
        # print("TO USER", self.user_id.login)
        template.send_mail(self.id,email_values={
            'email_to': self.user_id.login,
            'email_cc': self.email_from}
            ,force_send=True)
        # template_id = self.env['ir.model.data'].xmlid_to_res_id('helpdesk_lite.help_template_assign', raise_if_not_found=False)
        # if template_id:
        #     self.with_context(force_send=True,tracking_disable=True).message_post_with_template(template_id,email_layout_xmlid="helpdesk_lite.message_no_odoo_branding")

    def send_telegram(self,vals):
        url = "https://api.telegram.org/bot5468787671:AAEganNyqr3FPvYYuyEI3Ou_sFROmgzleLE/sendMessage"
        find = self.env['res.users'].search([('id','=',self.user_create.id)])
        asg = self.env['res.users'].search([('id','=',self.user_id.id)])
        stg = self.env['helpdesk_lite.stage'].search([('id','=',self.stage_id.id)])
        f_part = vals['partner_id']
        depart_p = self.env['res.users'].search([('partner_id','=',f_part)]).department
        depart = self.department or depart_p
        if stg.id == 1:
            payload = json.dumps({
                "text": stg.name+' '+"Request"+
                "\n"+"Ticket :"+' '+vals['code']+
                "\n"+"By :"+' '+str(find.name)+
                "\n"+"Department :"+' '+depart+
                "\n"+"Plant :"+' '+str(find.company_id.name)+
                "\n"+"Subject :"+' '+vals['name']+
                "\n"+"Request date :"+' '+str(datetime.today().strftime('%d-%m-%Y')),
                "chat_id": "-612370721"
                })
            headers = {
            'Content-Type': 'application/json'}
            response = requests.request("POST", url, headers=headers, data=payload)
        elif stg.id == 2:
            payload = json.dumps({
                "text": stg.name+' '+"Request\n"+"Ticket :"+' '+vals['code']+"\n"+"By :"+' '+str(find.name)+"\n"+"Department :"+' '+vals['department']+"\n"+"Plant :"+' '+str(find.company_id.name)+"\n""Subject :"+" "+vals['name']+
                "\n"+"Take by :"+' '+asg.name+"\n"+"Take date :"+' '+str(datetime.today().strftime('%d-%m-%Y')),
                "chat_id": "-612370721"
                })
            headers = {
            'Content-Type': 'application/json'}
            response = requests.request("POST", url, headers=headers, data=payload)
        elif stg.id == 3:
            payload = json.dumps({
                "text": stg.name+' '+"Request\n"+"Ticket :"+' '+vals['code']+"\n"+"By :"+' '+str(find.name)+"\n"+"Department :"+' '+vals['department']+"\n"+"Plant :"+' '+str(find.company_id.name)+"\n""Subject :"+" "+vals['name']
                +"\n"+"Solved by :"+' '+asg.name+"\n"+"Action :"+" "+vals['explain']+"\n"+"Solved date :"+' '+str(datetime.today().strftime('%d-%m-%Y')),
                "chat_id": "-612370721"
                })
            headers = {
            'Content-Type': 'application/json'}
            response = requests.request("POST", url, headers=headers, data=payload)
        elif stg.id == 4:
            payload = json.dumps({
                "text": stg.name+' '+"Request\n"+"Ticket :"+' '+vals['code']+"\n"+"By :"+' '+str(find.name)+"\n"+"Department :"+' '+vals['department']+"\n"+"Plant :"+' '+str(find.company_id.name)+"\n""Subject :"+" "+vals['name']+
                "\n"+"Cancel by :"+' '+asg.name+"\n"+"Action :"+" "+vals['explain']+"\n"+"Cancel date :"+' '+str(datetime.today().strftime('%d-%m-%Y')),
                "chat_id": "-612370721"
                })
            headers = {
            'Content-Type': 'application/json'}
            response = requests.request("POST", url, headers=headers, data=payload)

class MisUser(models.Model):
    _inherit = ['res.users']
    department = fields.Char()