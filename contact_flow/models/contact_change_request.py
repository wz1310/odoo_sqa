from odoo import fields, models, api, _
from datetime import datetime,timedelta,date
from odoo.exceptions import ValidationError,UserError
import datetime
import logging
import ast, json
_logger = logging.getLogger(__name__)

POP_LIST = ['activity_ids','activity_state','activity_user_id','activity_type_id','activity_date_deadline',
        'activity_summary','activity_exception_decoration','activity_exception_icon','message_is_follower','message_follower_ids',
        'message_partner_ids','message_channel_ids','message_ids','message_unread','message_unread_counter','message_needaction',
        'message_needaction_counter','message_has_error','message_has_error_counter','message_attachment_count','message_main_attachment_id',
        'website_message_ids','message_has_sms_error','create_uid','create_date','write_uid','write_date','__last_update','state','company_id']
        

class ContactChangeRequest(models.Model):
    _name = 'contact.change.request'
    _description = "Contact Change Request"
    _inherit = ["approval.matrix.mixin",'mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self:self.env['ir.sequence'].next_by_code('seq.contact.change.request'))

    partner_id = fields.Many2one('res.partner', string='Contact',required=True, track_visibility='onchange')
    field_id = fields.Many2one('ir.model.fields', string='Field', domain=[('model_id','=','res.partner')], track_visibility='onchange')
    model_name = fields.Char(related="field_id.relation", index=True, compute_sudo=True, store=True, track_visibility='onchange')
    field_type = fields.Selection(related="field_id.ttype", readonly=True)
    old_value_char = fields.Char(string='Old Value Char', track_visibility='onchange')

    old_value_m2o = fields.Integer("Old Value M2o")
    old_value_display = fields.Char("Old Value", compute="_compute_old_value_display", store=False)
    new_value_char = fields.Char("New Value")
    new_value_m2o = fields.Integer("New Value M2o")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submited', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('reject', 'Reject')
    ], string='State',default='draft',required=True, track_visibility='onchange')
    company_id = fields.Many2one('res.company', string="Company", required=True, ondelete="restrict", onupdate="restrict", default=lambda self:self.env.company.id, domain=False)

    auto_delete_oustand_approval = fields.Integer(related="company_id.auto_delete_oustand_approval", readonly=True)
    request_approval_expired = fields.Boolean(string="Request Approval Was Expired", default=False, compute="_compute_request_approval_expired")
    line_ids = fields.One2many('contact.change.request.line', 'contact_change_request_id', string='Lines')

    @api.constrains('field_id')
    def _constrains_field_id(self):
        for rec in self:
            rec._check_allowed_02m()
    
    def _compute_request_approval_expired(self):
        for rec in self:
            res = False
            if rec.state == 'submited':
                expiry_time = rec.write_date + timedelta(days=rec.auto_delete_oustand_approval)
                
                if expiry_time<=datetime.datetime.now():
                    res = True
            rec.request_approval_expired = res

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('seq.contact.change.request')
        result = super(ContactChangeRequest, self).create(vals)
        return result

    
    @api.depends('field_type','old_value_char','old_value_m2o')
    def _compute_old_value_display(self):
        for rec in self:
            if rec.field_type=='many2one':
                rec.old_value_display = self.env[rec.model_name].browse(rec.old_value_m2o).display_name
            else:
                rec.old_value_display = rec.old_value_char
    
    def _reset_field(self):
        self.update({'field_id':False})

    def _reset_m2o(self):
        self.update({'field_id':False,'old_value_m2o':False, 'new_value_m2o':False,'model_name':False})

    @api.onchange('partner_id')
    def onchange_partner(self):
        self._reset_m2o()
        
    
    @api.onchange('field_id')
    def _onchange_field_id(self):
        self._check_allowed_02m()
        if self.partner_id:
            partner_id = self.env['res.partner'].browse(self.partner_id.id)
            if self.field_id:
                if self.field_type == 'many2one':
                    old_value_m2o = getattr(self.partner_id,self.field_id.name).id
                    if old_value_m2o:
                        self.old_value_m2o = old_value_m2o
                    else:
                        self.old_value_m2o = False
                    
                    self.old_value_display = self.env[self.model_name].browse(self.old_value_m2o).display_name
                elif self.field_type == 'one2many':
                    self._get_data_o2m()
                else:
                    self.old_value_char = partner_id[self.field_id.name]
                    self.old_value_display = self.old_value_char
            else:
                self._reset_m2o()
        else:
            self._reset_m2o()

    def btn_submit(self):
        self.checking_approval_matrix()
        self.state = 'submited'

    def btn_approve(self):
        self.approving_matrix()
        if self.approved:
            if self.field_type in ['many2one']:
                new_value = self.new_value_m2o
                self.partner_id.write({
                    self.field_id.name : new_value
                })
            elif self.field_type in ['many2many']:
                new_value = self.new_value_m2o
                self.partner_id.write({
                    self.field_id.name : [(4,new_value)]
                })
            elif self.field_type == 'one2many':
                for rec in self.line_ids:
                    models = self.env[rec.model_name]
                    if rec.delete == True:
                        models = models.browse(eval(rec.values).get('id'))
                        models.sudo().unlink()
                    elif rec.is_update == True:
                        if rec.update_value:
                            models = models.browse(eval(rec.values).get('id'))
                            self.partner_id.sudo().message_post(body=self._get_message_update(rec.update_value,eval(rec.values).get('id')))
                            models.sudo().update(eval(rec.update_value))
                    elif rec.is_new == True:
                        dict_value = eval(rec.values)
                        for key, value in dict_value.items():
                            if type(value) == tuple:
                                dict_value[key] = value[0]
                        models.create(dict_value)

            else:
                new_value = self.new_value_char
                self.partner_id.write({
                    self.field_id.name : new_value
                })
            self.state = 'approved'

    def btn_reject(self):
        self.state = 'reject'
        self.rejecting_matrix()

    def btn_draft(self):
        self.state = 'draft'

    def _get_data_o2m(self):
        model = getattr(self.partner_id,self.field_id.name)
        line_ids = [(5,0,0)]
        for line in model.read():
            for key in list(line):
                if key in POP_LIST:
                    line.pop(key)
            data = {
                'values' : line,
                'model_name'  : self.model_name,
                'is_update' : False,
                'delete' : False,
            }
            line_ids.append((0,0,data))
        self.line_ids = line_ids

    def _get_message_update(self,update_value,id):
        body = '<span>'+self.field_id.field_description+' ('+getattr(self.env[self.model_name].browse(id),'display_name') +') :</span>'
        body += '<ul>'
        for k,v in eval(update_value).items():
            key = self._get_fields_string(self.env[self.model_name],k)
            old_value = getattr(self.env[self.model_name].browse(id),k) or ''
            new_value = str(v) or ''
            body += '<li>'+ key +' : ' + str(old_value) +' → '+ new_value +'</li>'
        body += '</ul>'
        return body

    def _get_fields_string(self,obj,fields):
        description = obj.fields_get([fields])
        description = description and description.get(fields, {})
        description = description and description.get('string', '') or ''
        return description

    def btn_open_new_line_form(self):
        return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                'views': [(False, 'form')],
                'res_model': self.model_name,
                'target': 'new',
                'context':{
                    'contact_change_request':True,
                    'default_partner_id':self.partner_id.id,
                    'model_name':self.model_name,
                    'request_id':self.id
                    }
            }

    def _get_allowed_o2m_fields(self):
        return ['partner_pricelist_ids','competitor_ids']
    
    def _check_allowed_02m(self):
        if self.field_id.name not in self._get_allowed_o2m_fields() and self.field_type == 'one2many':
            models = self.env['ir.model'].search([('model','=',self.model_name)])
            raise UserError(_("Cannot changed field relation with %s")%(models.name))

    @api.model
    def create_direct_form(self,vals,request_id,model_name):
        model = self.env[model_name].browse(vals)
        for line in model.read():
            for key in list(line):
                if key in POP_LIST:
                    line.pop(key)
            data = {
                'values' : line,
                'model_name'  : model_name,
                'is_update' : False,
                'delete' : False,
                'is_new':True
            }
        contact_change_request_id = self.env['contact.change.request'].browse(request_id)
        contact_change_request_id.line_ids = [(0,0,data)]
        model.sudo().unlink()
        return {'type': 'ir.actions.act_window_close'}

class ContactChangeRequestLine(models.Model):
    _name = 'contact.change.request.line'
    _description = "Contact Change Request Line"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    contact_change_request_id = fields.Many2one('contact.change.request', string='Contact Change Request')
    values = fields.Text(string='Value')
    model_name = fields.Char(string='Model',store=True)
    values_html = fields.Html(string='Values Html',compute='_compute_values_html')
    is_update = fields.Boolean(string='Update')
    delete = fields.Boolean(string='Delete')
    is_new = fields.Boolean(string='New')
    color = fields.Integer('Color Index', compute="change_colore_on_kanban")
    update_value = fields.Text(string='Update Value')
    state = fields.Selection(related='contact_change_request_id.state', string='State')

    def _compute_values_html(self):
        for rec in self:
            html = "<table>"
            models = self.env[rec.model_name]
            dict_value = eval(rec.update_value) if rec.update_value else {}
            update_value = [key for key in dict_value.keys()]
            for key, value in eval(rec.values).items():
                if type(value) == tuple:
                    value = value[1]
                if type(value) != list:
                    if update_value and key in update_value:
                        if 'pricelist_id' in dict_value:
                            price_name = models.pricelist_id.browse(dict_value.get('pricelist_id')).name
                        html += "<tr><td>"+models._fields[key].string+"</td><td>:</td><td><strike>"+str(value)+"</strike> → "+str(dict_value[key] if key !='pricelist_id' else price_name)+"</td></tr>"
                        # html += "<tr><td>"+models._fields[key].string+"</td><td>:</td><td><strike>"+str(value)+"</strike> → "+str(dict_value[key])+"</td></tr>"
                    else:
                        html += "<tr><td>"+models._fields[key].string+"</td><td>:</td><td>"+str(value)+"</td></tr>"
                    
            html += "/<table>"
            rec.values_html = html

    def btn_delete(self):
        self.delete = True

    def btn_undelete(self):
        self.delete = False

    def btn_update(self):
        view = self.env.ref('contact_flow.contact_change_request_line_field_view_form')
        return {
                'name': _('Changed Field'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                'views': [(view.id, 'form')],
                'res_model': 'contact.change.request.line.field',
                'target': 'new',
                'context': {'id':self.id,'model_name':self.model_name,'values':self.values},
            }

    def change_colore_on_kanban(self):
        for record in self:
            color = 0
            if record.delete == True:
                color = 1
            record.color = color

class ContactChangeRequestLineField(models.Model):
    _name = 'contact.change.request.line.field'

    def _get_context_model(self):
        return [('model_id','=',self._context.get('model_name'))]

    field_id = fields.Many2one('ir.model.fields', string='Field', domain=_get_context_model, track_visibility='onchange')
    model_name = fields.Char(related="field_id.relation", index=True, compute_sudo=True, store=True, track_visibility='onchange')
    field_type = fields.Selection(related="field_id.ttype", readonly=True)
    old_value_char = fields.Char(string='Old Value Char', track_visibility='onchange')

    old_value_m2o = fields.Integer("Old Value M2o")
    old_value_display = fields.Char("Old Value", compute="_compute_old_value_display", store=False)
    new_value_char = fields.Char("New Value")
    new_value_m2o = fields.Integer("New Value M2o")

    @api.depends('field_type','old_value_char','old_value_m2o')
    def _compute_old_value_display(self):
        for rec in self:
            if rec.field_type=='many2one':
                rec.old_value_display = self.env[rec.model_name].browse(rec.old_value_m2o).display_name
            else:
                rec.old_value_display = rec.old_value_char

        
    def _reset_field(self):
        self.update({'field_id':False})

    def _reset_m2o(self):
        self.update({'field_id':False,'old_value_m2o':False, 'new_value_m2o':False,'model_name':False})
    
    @api.onchange('field_id')
    def _onchange_field_id(self):
        values = self._context.get('values')
        if values:
            model_id = self.env[self._context.get('model_name')].browse(eval(values).get('id'))
            if self.field_id:
                if self.field_type == 'many2one':
                    old_value_m2o = getattr(model_id,self.field_id.name).id
                    if old_value_m2o:
                        self.old_value_m2o = old_value_m2o
                    else:
                        self.old_value_m2o = False
                    
                    self.old_value_display = self.env[self.model_name].browse(self.old_value_m2o).display_name
                else:
                    self.old_value_char = model_id[self.field_id.name]
                    self.old_value_display = self.old_value_char
            else:
                self._reset_m2o()
        else:
            self._reset_m2o()

    def confirm(self):
        contact_change_request_id = self.env['contact.change.request.line'].browse(self._context.get('id'))
        update_value = eval(contact_change_request_id.update_value) if contact_change_request_id.update_value else {}
        update_value[self.field_id.name] = self.new_value_m2o if self.field_type == 'many2one' else self.new_value_char
        contact_change_request_id.update_value = update_value
        contact_change_request_id.is_update = True