from odoo import fields, models, api, _
from odoo.exceptions import ValidationError,UserError
import xml.etree as etr
import xml.etree.ElementTree as ET
from ast import literal_eval
import logging
_logger = logging.getLogger(__name__)
from odoo.tools.misc import formatLang, format_date

class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = ["res.partner","approval.matrix.mixin"]

    customer = fields.Boolean(string='Customer', default=False)
    supplier = fields.Boolean(string='Supplier', default=False)
    code = fields.Char(string='Code')
    vat = fields.Char(string='Tax ID')
    national_id = fields.Char(string='NIK')
    active = fields.Boolean(string='Active',default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('reject', 'Reject'),
    ], string='State',required=True,default='draft')
    document_ids = fields.One2many('res.partner.document', 'partner_id', string='Documents')
    approvers_ids = fields.Many2many('res.users',string="Approver User", compute='_compute_approvers_ids', store=False, search='_search_approver_ids')

    join_date = fields.Date(string="Join Date", required=False, defaut=False)
    owner_image = fields.Binary(string='Owner',store=True)
    owner_file_name = fields.Char(string='Filename Owner',store=True)
    warehouse_image = fields.Binary(string='Warehouse Image',store=True)
    warehouse_file_name = fields.Char(string='Filename Owner',store=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)

    first_sales_transaction_date = fields.Char(compute="_compute_first_sales_transaction_date")

    operating_unit_id = fields.Many2one('res.branch', string='Operating Unit')

    def _compute_first_sales_transaction_date(self):
        for rec in self:
            formated_date = '-'
            if rec.customer==True and rec.sale_order_count:
                first_order = rec.sale_order_ids.sorted('id')[0]
                # rec.first_transaction_date = formatLang(self.env, first_order.create_date.strftime('%Y-%m-%d'), digits=None, grouping=True, monetary=False, dp=False, currency_obj=False)
                formated_date = format_date(self.env, first_order.create_date.strftime('%Y-%m-%d'), lang_code=False, date_format=False)
            
            rec.first_sales_transaction_date = formated_date


    # disable join date
    # @api.constrains('join_date')
    # def constrains_join_date(self):
    #     for rec in self:
    #         if not rec.join_date:
    #             rec.join_date = rec.create_date.strftime('%Y-%m-%d')

    def validate_vat(self,vals):
        for rec in self:
            # if vals and len(vals)!=15:
            # update vat into 16 digit by andri 22 juli 2022
            if vals and len(vals)!=16:
                raise UserError(_("%s for %s must be 16 digit!") % (rec._fields.get('vat'). string,rec.name))
    
    @api.constrains('code')
    def constrains_code(self):
        for rec in self:
            rec.ref = rec.code
    
    def name_get(self):
        res = []
        for rec in self:
            name = "%s%s" % ("["+rec.ref+"] " if rec.ref else "", rec.name, )
            res += [(rec.id, name)]
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        connector = '|'
        recs = self.search([connector, ('ref', operator, name), ('name',operator,name)] + args, limit=limit)
        return recs.name_get()

    @api.constrains('vat')
    def constrains_vat(self):
        # if only filled will validated
        for rec in self:
            rec.filtered(lambda r:r.vat and len(r.vat)>0).validate_vat(rec.remove_non_numeric(rec.vat))

    @api.onchange('vat')
    def onchange_vat(self):
        # if only filled
        if self.vat:
            text_vat = ''
            for idx, val in enumerate(self.remove_non_numeric(self.vat)):
                if val.isnumeric():
                    text_vat += val
                    if idx in (1,4,7,11):
                        text_vat += '.'
                    if idx == 8:
                        text_vat += '-'
            self.validate_vat(self.remove_non_numeric(text_vat))
            self.vat = text_vat
    
    def remove_non_numeric(self,value):
        text_val = ''
        if value:
            for idx, val in enumerate(value):
                if val.isnumeric():
                    text_val += val
        return text_val

    
    @api.depends('approval_ids')
    def _compute_approvers_ids(self):
        for rec in self:
            rec.approvers_ids = rec.approval_ids.mapped('approver_ids')
    

    def checking_pricelist_ids(self):
        self.ensure_one()
        if not len(self.partner_pricelist_ids):
            raise UserError(_("Please fill pricelist!"))
        divisions = self.env['crm.team'].search([])
        line_divisions = self.partner_pricelist_ids.mapped('team_id')
        
        if len(divisions)!=len(line_divisions):
            substract = divisions-line_divisions
            raise UserError(_("Please fill all pricelist for %s division!") % (", ".join(substract.mapped('display_name')),))
    

    def _checking_documents(self):
        self.ensure_one()
        doc_fields = self.env['res.partner.document.field'].search([])

        mandatory_fields = doc_fields.filtered(lambda r:r.mandatory==True)
        required_warns = []
        if len(mandatory_fields):
            
            for each in mandatory_fields:
                filled = self.document_ids.filtered(lambda r:r.field_id.id==each.id)
                if not len(filled):
                    required_warns.append(each.name)

        if len(required_warns):
            raise UserError(_("Please fill following required documents:\n%s") % ("\n".join(required_warns),))
    
    def btn_submit(self):
        # self.checking_pricelist_ids()
        self._checking_documents()
        self.state = 'waiting_approval'
        self.with_context(force_company=False).checking_approval_matrix()


    def auto_approve_user(self):
        # only if creating user
        recs = self.filtered(lambda r:r.active == True and len(r.user_ids) and r.state in ['draft'])
        recs.state = 'approved'
        for rec in recs:
            rec.message_post(body="Partner Created as User")

    @api.constrains('active')
    def _constrains_active(self):
        # only for customer
        self.auto_approve_user()

    # @api.constrains('customer','supplier')
    # def constrains_customer_supplier(self):
    #     supplier_only = self.filtered(lambda r:r.supplier and not r.customer and r.state=='draft')
    #     if len(supplier_only):
    #         # if new contact is supplier then state will be automatically set to "approved"
    #         supplier_only.write({'state':'approved'})

    def btn_approve(self):
        self._fetch_sequence()
        contacts = self.search([('parent_id','in',self.ids),'|', ('active','=',False), ('active','=',True)])
        self.write({'state':'approved','active':True})
        contacts.write({'state':'approved', 'active':True, 'join_date':fields.Date.today()})


    def btn_draft(self):
        self.update({
            'state':'draft',
            'active':True
        })

    def btn_reject(self):
        contacts = self.search([('parent_id','in',self.ids),'|', ('active','=',False), ('active','=',True)])
        contacts.write({'state':'reject','active':False})
        self.state = 'reject'

    def open_reject_message_wizard(self):
        self.ensure_one()
        
        form = self.env.ref('approval_matrix.message_post_wizard_form_view')
        context = dict(self.env.context or {})
        context.update({'default_prefix_message':"<h4>Rejecting Contact</h4>","default_suffix_action": "btn_reject"}) #uncomment if need append context
        context.update({'active_id':self.id,'active_ids':self.ids,'active_model':'res.partner'})
        res = {
            'name': "%s - %s" % (_('Rejecting Contact'), self.name),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'message.post.wizard',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res

    def _fetch_sequence(self):
        sequence_obj = self.env['ir.sequence']
        if not self.code:
            if self.operating_unit_id.id and self.operating_unit_id.sequence_id.id:
                self.code = self.operating_unit_id.sequence_id._next()
                return None
            #Change by Adi, Supplier tidak Auto Number dan tanpa pilih Company (26 Oktober 2020)
            if self.supplier:
                return None
            if self.company_id:
                code = ''
                if self.customer:
                    code = sequence_obj.with_context(force_company=self.company_id.id).sudo().next_by_code('seq.customer.empty')
                # elif self.supplier:
                #     code = sequence_obj.with_context(force_company=self.company_id.id).sudo().next_by_code('seq.supplier.empty')
                self.code = code
            # else:
            #     raise UserError(_("Please Set Company"))
        return None

    # ,('state','=', 'waiting_approval'),('active','=',False)
    def _search_approver_ids(self, operator, value):
        query = """ 
            SELECT doc.res_id 
            FROM approval_matrix_document_approval doc 
            JOIN approval_matrix_doc_approval_user_rel users ON users.approval_id = doc.id AND users.user_id = %s 
            JOIN res_partner partner ON doc.res_id = partner.id
            WHERE res_model = 'res.partner' AND partner.state = 'waiting_approval'
            """

        self._cr.execute(query, (value,))
        res = self._cr.fetchall()
        if not res:
            return [('id','=',False)]
        return [('id', operator, [r[0] for r in res])]

    def __authorized_form(self, root):
        
          
        def append_readonly_attrs(elm, readonly_domain=[('state','not in',['draft','waiting_approval'])]):
            
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
                'partner_pricelist_discount_ids':[('state','not in',['draft','approved'])],
                # 'partner_pricelist_ids':[('state','not in',['draft','approved'])],
            }
            for elm in elms:
                if elm.tag=='field':
                    readonly_domain = special_domain.get(elm.get('name'), [('state','not in',['draft','waiting_approval'])])
                    elm = append_readonly_attrs(elm, readonly_domain)
                else:
                    if len(elm)>0:
                        
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
                # child = append_readonly_attrs(child)
                child = set_readonly_on_fields(child)
        return root

    def _get_fields_string(self,obj,fields):
        description = obj.fields_get([fields])
        description = description and description.get(fields, {})
        description = description and description.get('string', '') or ''
        return description

    def _message_fields_many(self,str_ids,obj,vals):
        info = {
            0: _('Created New Line '+str_ids),
            1: _('Updated Line '+str_ids),
            2: _('Removed Line '+str_ids),
            3: _('Removed Line '+str_ids),
            6: _('many2many'),
        }
        body=''
        for val in vals:
            if val and info.get(val[0], False):
                if val[2]:
                    for value in val[2]:
                        if val[0] ==  0:
                            body += info[0]
                        elif val[0] == 1:
                            body += info[1]
                        
                        try:
                            if type(val)==list and val[0]==0 and len(val)==3:
                                if type(val[2])==dict:
                                    for k,v in val[2].items():
                                        body += "<li>%s:%s</li>" % (k,v)
                            else:
                                if obj._fields[value].type == 'many2one':
                                    body += self._get_message_many2one(obj.browse(val[1]),val[2],value)
                                else:
                                    body += self._get_message(obj.browse(val[1]),val[2],value)    
                        except Exception as e:
                            
                                body += "%s" % (str(val[2]))
                        
                else:
                    body += '<li>'+info[2] + obj.browse(val[1]).display_name+'</li>'
        return body
    
    def _get_message_many2one(self,obj,vals,value):
        body=''
        old_value = getattr(obj,value).display_name or ''
        new_value = getattr(obj,value).browse(vals[value]).display_name or ''
        body += '<li>'+self._get_fields_string(obj,value) +' : ' + old_value +' → '+ new_value +'</li>'
        return body
    
    def _get_message(self,obj,vals,value):
        body=''   
        try:
            old_value = getattr(obj,value) or ''
            new_value = vals[value] or ''
            body += '<li>'+self._get_fields_string(obj,value) +' : ' + str(old_value) +' → '+ str(new_value) +'</li>'
        except Exception as e:
            
            if type(value)==dict:
                for k,v in value.items():
                    body += "<li>%s:%s</li>" % (k,str(v))
                
        return body
    
    def write(self, vals):
        for rec in self:
            body = ''
            body += '<ul>'
            for value in vals:
                if self._fields[value].type == 'many2one':
                    body += rec._get_message_many2one(rec,vals,value)
                elif self._fields[value].type in 'one2many':
                    
                    obj = self.env['ir.model.fields'].search([('model_id','=','res.partner'),('name','=',value)]).relation
                    
                    body += self._message_fields_many(self._get_fields_string(self,value),self.env[obj],vals[value])
                elif self._fields[value].type == 'binary':
                    body += ''
                else:
                    
                    body += self._get_message(self,vals,value)
            body += '</ul>'
            rec.message_post(body=body)
            rec._change_uppercase_char(vals)
        return super(ResPartner,self).write(vals)


    @api.model
    def create(self, vals):
        self._change_uppercase_char(vals)
        return super(ResPartner,self).create(vals)

    def _change_uppercase_char(self,vals):
        upper_list = ['city','code','name','ref','street','street2','tax_holder_address','tax_holder_name']
        for k,v in vals.items():
            if k in upper_list:
                if v:
                    vals[k] = v.upper()

    @api.model
    def _fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):

        sup = super()._fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        # get generated xml view
        
        # if form
        if view_type=='form':
            root_elm = ET.fromstring("%s" % (sup['arch']))
            # AUTHORIZED ALL "<field>" element
            new_view = self.__authorized_form(root_elm)
            sup.update({'arch':ET.tostring(new_view)})

        return sup

class ResPartnerDocument(models.Model):
    _name = 'res.partner.document'

    partner_id = fields.Many2one('res.partner', string='Contact')
    field_id = fields.Many2one('res.partner.document.field', string='File Name')
    file = fields.Binary(string='Attachment',attachment=False)


class ResPartnerDocumentField(models.Model):
    _name = 'res.partner.document.field'

    name = fields.Char(string='Name',required=True)
    mandatory = fields.Boolean(string='Mandatory',default=True)

    _sql_constraints = [
        ('name_field_unique', 'unique (name)', 'Constrains failed name must be unique')
    ]