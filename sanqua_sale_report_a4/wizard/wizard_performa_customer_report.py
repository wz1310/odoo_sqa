# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

class PerformaCustomerReportWizard(models.TransientModel):
    _name = 'performa.customer.report.wizard'
    _description = 'Wizard Performa Customer Report'

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')


    def btn_confirm(self):
        tree = self.env.ref('sanqua_sale_report_a4.performa_customer_report_tree')
        context = dict(self.env.context or {})
        context.update({'start_date':self.start_date,'end_date':self.end_date})
        self.env['report.performa.customer'].with_context(context).init()
        res = {
            'name': "%s" % (_('Performa Customer Report')),
            'view_mode': 'tree',
            'res_model': 'report.performa.customer',
            'views': [(tree.id,'tree')],
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'current'
        }
        return res

    