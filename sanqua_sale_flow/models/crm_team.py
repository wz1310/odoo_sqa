# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError

import logging
_logger = logging.getLogger(__name__)

import xml.etree as etr
import xml.etree.ElementTree as ET
from ast import literal_eval


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    name = fields.Char(string='Name',track_visibility='onchange')
    use_quotations = fields.Boolean(string='Quotations',track_visibility='onchange')
    user_id = fields.Many2one('res.users', string='Supervisor',track_visibility='onchange')
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms',track_visibility='onchange')
    invoice_target = fields.Integer(string='Invoicing Target',track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company',track_visibility='onchange')
    branch_id = fields.Many2one('res.branch', string='Operating Unit',track_visibility='onchange')
    member_ids = fields.One2many('res.users', 'sale_team_id', string='Team Members', domain=[],track_visibility='onchange')
    product_category_ids = fields.Many2many('product.category', string='Allowed Product Category',track_visibility='onchange')
    sales_user_ids = fields.Many2many('res.users','sales_team_users_rel','team_id','user_id', string='Sales User',track_visibility='onchange')
    sales_admin_ids = fields.Many2many('res.users','crm_team_sales_admin_rel','crm_team_id', 'user_id',string='Sales Admin',track_visibility='onchange')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancel')
    ], string='State',default='draft',track_visibility='onchange')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')

    def btn_submit(self):
        self.state = 'done'

    def btn_cancel(self):
        self.state = 'cancel'

    def btn_draft(self):
        self.state = 'draft'
        
    @api.model
    @api.returns('self', lambda value: value.id if value else False)
    def _get_default_team_id(self, user_id=None, domain=None):
        if domain:
            return super(CrmTeam, self)._get_default_team_id(user_id, domain)
        
    allowed_partner_ids = fields.Many2many('res.partner',compute='_compute_allowed_partner_ids', string='Allowed Partner')
    
    def _read(self, fields):
        return super(CrmTeam, self.sudo())._read(fields)


    def __authorized_form(self, root):
        def append_nocreate_options(elm):
            
            fields_name = elm.attrib.get('name')

            Many2one = isinstance(self._fields[fields_name], fields.Many2one)
            Many2many = isinstance(self._fields[fields_name], fields.Many2many)
            One2many = isinstance(self._fields[fields_name], fields.One2many)
            if elm.tag!='field':
                return elm
            
            fields_name = elm.attrib.get('name')

            Many2one = isinstance(self._fields[fields_name], fields.Many2one)
            Many2many = isinstance(self._fields[fields_name], fields.Many2many)
            if elm.tag!='field':
                return elm
            options = elm.get('options')
            if options:
                if (Many2one or Many2many or One2many):
                    # IF HAS EXISTING "attrs" ATTRIBUTE
                    options_dict = literal_eval(options)
                    options_nocreate = options_dict.get('no_create')
                
                    # if had existing readonly rules on attrs will append it with or operator
                    options_dict.update({"no_create":1})
            else:
                if (Many2one or Many2many):
                    options_dict = {"no_create":1}
                    
            try:
                new_options_str = str(options_dict)
                elm.set('options',new_options_str)
                
            except Exception as e:
                pass
            return elm	
            
        def set_nocreate_on_fields(elms):
            for elm in elms:
                if elm.tag=='field':
                    elm = append_nocreate_options(elm)
                else:
                    if len(elm)>0:
                        _logger.info((len(elm)))
                        # if elm.tag in ['tree','kanban','form','calendar']:
                        # 	continue # skip if *2many field child element
                        elm = set_nocreate_on_fields(elm)
                    else:
                        if elm.tag=='field':
                            elm = append_nocreate_options(elm)
            return elms
        
        def append_readonly_limit_approval(elm):
            if elm.tag!='field':
                return elm

            attrs = elm.get('attrs')
            if attrs:
                # IF HAS EXISTING "attrs" ATTRIBUTE
                attrs_dict = literal_eval(attrs)
                attrs_readonly = attrs_dict.get('readonly')
                # if had existing readonly rules on attrs will append it with or operator
                if attrs_readonly:
                    if type(attrs_readonly) == list:
                        # readonly if limit_approval_state not in draft,approved
                        # incase:
                        # when so.state locked (if limit automatically approved the limit_approval_state will still in draft) so will use original functions
                        # when so.state == draft and limit approval strate in (need_approval_request,  need_approval, reject) will lock the field form to readonly
                        attrs_readonly.insert(0,('limit_approval_state','not in',['draft']))
                        attrs_readonly.insert(0,'|')
                    attrs_dict.update({'readonly':attrs_readonly})
                else:
                    # if not exsit append new readonly key on attrs
                    attrs_dict.update({'readonly':[('limit_approval_state','not in',['draft'])]})
            else:
                attrs_dict = {'readonly':[('limit_approval_state','not in',['draft'])]}
            try:
                new_attrs_str = str(attrs_dict)
                elm.set('attrs',new_attrs_str)
            except Exception as e:
                pass

            return elm

        def append_readonly_attrs(elm, readonly_domain=[('state','not in',['draft'])]):
            if elm.tag!='field':
                return elm
            
            attrs = elm.get('attrs')
            
            if attrs:
                # IF HAS EXISTING "attrs" ATTRIBUTE
                attrs_dict = literal_eval(attrs)
                attrs_readonly = attrs_dict.get('readonly')
                # if had existing readonly rules on attrs will append it with or operator
                
                if attrs_readonly:
                    attrs_dict.update({'readonly':readonly_domain})
                else:
                    # if not exsit append new readonly key on attrs
                    attrs_dict.update({'readonly':readonly_domain})
            else:
                attrs_dict = {'readonly':readonly_domain}
            try:
                new_attrs_str = str(attrs_dict)
                elm.set('attrs',new_attrs_str)
            except Exception as e:
                pass

            return elm

        def set_readonly_on_fields(elms):
            special_domain = {
                # 'partner_pricelist_discount_ids':[('state','not in',['draft','approved'])],
                # 'partner_pricelist_ids':[('state','not in',['draft','approved'])],
            }
            for elm in elms:
                if elm.tag=='field':
                    readonly_domain = special_domain.get(elm.get('name'), [('state','not in',['draft'])])
                    elm = append_readonly_attrs(elm, readonly_domain)
                else:
                    if len(elm)>0:
                        _logger.info((len(elm)))
                        if elm.tag in ['tree','kanban','form','calendar']:
                            continue # skip if *2many field child element
                        elm = set_readonly_on_fields(elm)
                    else:
                        if elm.tag=='field':
                            elm = append_readonly_attrs(elm)
            return elms

        # form = root.find('form')
        paths = []
        for child in root:
            
            if child.tag=='sheet':
                
                child = set_readonly_on_fields(child)
                child = set_nocreate_on_fields(child)
        return root

    @api.model
    def _fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):

        sup = super()._fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        # get generated xml view
        
        # if form
        if view_type=='form':
            root_elm = ET.fromstring("%s" % (sup['arch']))
            # AUTHORIZED ALL "<field>" element
            new_view = self.__authorized_form(root_elm)
            # print (new_view,'LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLl')
            sup.update({'arch':ET.tostring(new_view)})

        return sup
    
    def _compute_allowed_partner_ids(self):
        print("CONTEKK",self._context)
        for rec in self:
            rec.allowed_partner_ids = False
            query = """
                    SELECT pp.partner_id FROM partner_pricelist pp
            LEFT JOIN crm_team ct  ON pp.team_id = ct.id WHERE pp.team_id = %s;
            """
            rec.env.cr.execute(query, (rec.id,))
            res = rec.env.cr.fetchall()
            
            ids = [row[0] for row in res]
            print("ID CRM", ids)
            if len(ids):
                rec.allowed_partner_ids = [(6,0,ids)]
            


class ResUsers(models.Model):
    _inherit = 'res.users'

    def _compute_sale_team_ids(self):
        # teams = self.env['crm.team']
        
        def find_team(user):
            Team = self.env['crm.team']
            teams = Team.search([])
            res = Team
            for team in teams:
                if user.id in team.sales_user_ids.ids:
                    res+=team
            return res
        for rec in self:
            teams = find_team(rec)
            rec.sale_team_ids = teams