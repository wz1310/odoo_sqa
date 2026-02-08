# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError
import xml.etree as etr
import xml.etree.ElementTree as ET

class AccountMove(models.Model):
    _inherit = 'account.move'


    def __authorized_form(self, root):
        due_date_filter = self.env['account.move.due.date.filter'].search([('active','=',True)])
        for rec in due_date_filter:
            new_filter = ET.Element('filter')
            new_filter.set('name',rec.name)
            start_date = _("(context_today()+datetime.timedelta(days=%s))") % (str(rec.start_date)) + ".strftime('%Y-%m-%d')"
            end_date = _("(context_today()+datetime.timedelta(days=%s))") % (str(rec.end_date)) + ".strftime('%Y-%m-%d')"
            new_filter.set('domain',_("[('invoice_date_due','>=',%s),('invoice_date_due','<=',%s)]") % (start_date,end_date))
            root.append(new_filter)
        return root

    @api.model
    def _fields_view_get(self, view_id=None, view_type='form', toolbar=True, submenu=False):
        sup = super()._fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        
        if view_type=='search':
            root_elm = ET.XML("%s" % (sup['arch']))
            new_view = self.__authorized_form(root_elm)
            sup.update({'arch':ET.tostring(new_view)})

        return sup