# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError,ValidationError,Warning

_logger = logging.getLogger(__name__)


class InvoiceCollectionWizard(models.TransientModel):
    _name = 'invoice.collection.wizard'
    _description = 'Invoice Collection Wizard'

    def _domain_invoices_ids(self):
        # allowed_invoice_ids = self.env['report.invoice.position'].search(['|',('line_id','=',False),('state','in',['done']),('company_id','=',self.env.company.id)]).mapped('invoice_id')
        # invoices_ids = allowed_invoice_ids.filtered(lambda r: r.type == 'out_invoice' and r.state not in ['draft','cancel'])
        # return [('id','in',invoices_ids.ids)]
        # update Andri 07 Juni 2022
        sql = """SELECT inv.ID AS id,inv.ID AS invoice_id,inv.type,inv.state AS inv_state,
            inv.partner_id AS partner_id,cal_s.activity_id AS activity_id,cal_s.line_id AS line_id,
            ca_state,cal_s.collector_id AS collector_id,inv.company_id AS company_id
            FROM
            account_move AS inv LEFT JOIN (
            SELECT DISTINCT ON
            ( cal.invoice_id ) cal.ID AS line_id,ca.ID AS activity_id,ca.state as ca_state,
            ca.collector_id,cal.invoice_id
            FROM
            collection_activity_line cal
            JOIN
            collection_activity ca
            ON
            ca.ID = cal.activity_id
            ORDER BY
            cal.invoice_id DESC,
            ca.activity_date)
            cal_s ON cal_s.invoice_id = inv.ID
            WHERE
            (line_id is null OR ca_state='done')
            AND company_id ="""+str(int(self.env.company.id))+"""
            AND inv.type = 'out_invoice'
            AND inv.state not in ('draft','cancel')"""
        cr= self.env.cr
        cr.execute(sql,())
        result= cr.fetchall()
        find_res = [x[0] for x in result]
        return [('id','in',find_res)]

    activity_id = fields.Many2one('collection.activity', string='Collection')
    invoice_ids = fields.Many2many('account.move', string='Invoice', domain=_domain_invoices_ids)

    def confirm(self):
        # if self.check_gap_date(self.invoice_ids):
        #     raise UserError(_("Any gap date in list of invoice."))
        # else:
        #     vals = []
        #     for rec in self.invoice_ids:
        #         if not self.check_allowed_invoice(rec):
        #             data = {
        #                 'activity_id':self.activity_id.id,
        #                 'invoice_id':rec.id,
        #                 'partner_id':rec.partner_id.id
        #             }
        #             vals.append(data)

        #     self.env['collection.activity.line'].create(vals)
        ##edited by dion 27 maret 2020##
        vals = []
        for rec in self.invoice_ids:
            if not self.check_allowed_invoice(rec):
                data = {
                    'activity_id':self.activity_id.id,
                    'invoice_id':rec.id,
                    'partner_id':rec.partner_id.id
                }
                vals.append(data)

        self.env['collection.activity.line'].create(vals)
    def check_gap_date(self,invoice_ids):
        gap = False
        date = ''
        for rec in invoice_ids:
            if isinstance(date, str):
                date = rec.invoice_date
            else:
                gap_date = date-rec.invoice_date
                if gap_date.days > 1:
                    gap = True
                else:
                    date = rec.invoice_date
        return gap
    
    @api.model
    def check_allowed_invoice(self,invoice_id):
        # allowed_invoice_ids = self.env['report.invoice.position'].search(['|',('line_id','=',False),('state','in',['done'])]).invoice_id
        # if invoice_id not in allowed_invoice_ids:
        #     raise UserError(_('This invoice %s already proccessed in another collection.') % (invoice_id.name))
        # else:
        #     return False
        # Update by Andri 09 Jun 2022
        res = []
        sql = """SELECT inv.ID AS id,inv.ID AS invoice_id,inv.type,inv.state AS inv_state,
            inv.partner_id AS partner_id,cal_s.activity_id AS activity_id,cal_s.line_id AS line_id,
            ca_state,cal_s.collector_id AS collector_id,inv.company_id AS company_id
            FROM
            account_move AS inv LEFT JOIN (
            SELECT DISTINCT ON
            ( cal.invoice_id ) cal.ID AS line_id,ca.ID AS activity_id,ca.state as ca_state,
            ca.collector_id,cal.invoice_id
            FROM
            collection_activity_line cal
            JOIN
            collection_activity ca
            ON
            ca.ID = cal.activity_id
            ORDER BY
            cal.invoice_id DESC,
            ca.activity_date)
            cal_s ON cal_s.invoice_id = inv.ID
            WHERE
            (line_id is null OR ca_state='done')"""
        cr= self.env.cr
        cr.execute(sql,())
        result= cr.fetchall()
        find_allowed_invoice_ids = [x[1] for x in result]
        if invoice_id.id not in find_allowed_invoice_ids:
            raise UserError(_('This invoice %s already proccessed in another collection.') % (invoice_id.name))
        else:
            return False