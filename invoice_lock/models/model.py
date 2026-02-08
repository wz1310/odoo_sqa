from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

import xml.etree as etr
import xml.etree.ElementTree as ET
from ast import literal_eval

class AccountMove(models.Model):
    _inherit = 'account.move'


    locked = fields.Boolean(string="Locked", compute="_compute_locked", inverse="_inverse_locked", default=False, store=True, track_visibility="onchange")

    def btn_unlock(self):
        self.filtered(lambda r:r.locked and r.state == 'draft').write({'locked':False})

    def btn_lock(self):
        self.filtered(lambda r:r.locked==False).write({'locked':True})

    def button_draft(self):
        print("========locket============")
        self.write({'locked':False})
        return super().button_draft()

    def action_post(self):
        print("===========B==========")
        self.update({'locked':True})
        return super().action_post()


    @api.depends('type')
    def _compute_locked(self):
        # locked when not draft OR (invoice is customer invoice)
        not_draft = self.filtered(lambda r:r.state!='draft')
        draft_out_invoice = self.filtered(lambda r: r.state=='draft' and r.type=='out_invoice')


        (not_draft+draft_out_invoice.filtered(lambda r:r.id)).update({'locked':True})
        should_open = (self - not_draft - draft_out_invoice).update({'locked':False})
    
    def _inverse_locked(self):
        
        return True
    
    def __lock_form(self, root):
        # res = super().__authorized_form(root)

        def append_nocreate_options(elm):
            # _logger.info(('---- loop', elm.tag,elm.attrib.get('name')))
            
            fields_name = elm.attrib.get('name')

            Many2one = isinstance(self._fields[fields_name], fields.Many2one)
            Many2many = isinstance(self._fields[fields_name], fields.Many2many)
            # One2many = isinstance(self._fields[fields_name], fields.One2many)
            if elm.tag!='field':
                return elm
            
            fields_name = elm.attrib.get('name')

            Many2one = isinstance(self._fields[fields_name], fields.Many2one)
            Many2many = isinstance(self._fields[fields_name], fields.Many2many)
            if elm.tag!='field':
                return elm
            options = elm.get('options')
            if options:
                if (Many2one or Many2many):
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
        
        def append_readonly_on_locked(elm):
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
                        # readonly if locked==True not in draft,approved
                        attrs_readonly.insert(0,('locked','=',True))
                        attrs_readonly.insert(0,'|')
                    attrs_dict.update({'readonly':attrs_readonly,'force_save':1})
                else:
                    # if not exsit append new readonly key on attrs
                    attrs_dict.update({'readonly':[('locked','=',True)],'force_save':1})
            else:
                attrs_dict = {'readonly':[('locked','=',True)],'force_save':1}
            try:
                new_attrs_str = str(attrs_dict)
                elm.set('attrs',new_attrs_str)
            except Exception as e:
                pass

            return elm


        def set_readonly_on_fields(elms):
            for elm in elms:
                if len(elm)>0:
                    _logger.info("has %s child(s)" % (len(elm)))
                    if elm.tag in ['tree','kanban','form','calendar']:
                        continue # skip if *2many field child element
                    if elm.tag == 'field': # indicates X2many field
                        elm = append_readonly_on_locked(elm)
                    else:
                        elm = set_readonly_on_fields(elm)
                else:
                    if elm.tag=='field':
                        # elm = append_readonly_on_locked(elm)
                        
                        # elm.set('readonly','True')
                        elm = append_readonly_on_locked(elm)
            return elms

        
        # form = root.find('form')
        paths = []
        for child in root:
            
            if child.tag=='sheet':
                # child = append_readonly_on_locked(child)
                
                child = set_readonly_on_fields(child)
                child = set_nocreate_on_fields(child)
        return root

    @api.model
    def _fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        sup = super()._fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)

        # if form
        if view_type=='form':
            root_elm = ET.fromstring("%s" % (sup['arch']), parser=ET.XMLParser(encoding='utf-8'))
            # AUTHORIZED ALL "<field>" element
            new_view = self.__lock_form(root_elm)
            sup.update({'arch':ET.tostring(new_view)})

        return sup

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    locked = fields.Boolean(string="Loced", related="move_id.locked", readonly=True)