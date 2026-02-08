# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models
import datetime
from calendar import monthrange

_logger = logging.getLogger(__name__)

class PerformaSalesmanReportWizard(models.TransientModel):
    _name = 'performa.salesman.report.wizard'
    _description = 'Wizard Performa Salesman Report'

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    tahun = fields.Integer(string='Tahun')
    bulan = fields.Integer(string='Bulan (1-12)')

    @api.onchange('start_date','end_date')
    def _onchange_date(self):
        if self.start_date:
            self.start_date = datetime.date(self.start_date.year, self.start_date.month,1)
        if self.end_date:
            self.end_date =  datetime.date(self.end_date.year, self.end_date.month,monthrange(self.end_date.year, self.end_date.month)[1])


    def btn_confirm(self):
        pivot = self.env.ref('sanqua_sale_report_a12.performa_salesman_report_pivot')
        context = dict(self.env.context or {})
        context.update({'start_date':self.start_date,'end_date':self.end_date,'bulan':self.bulan,'tahun':self.tahun})
        self.env['report.performa.salesman'].with_context(context).init()
        res = {
            'name': "%s" % (_('Performa Salesman Report')),
            'view_mode': 'pivot',
            'res_model': 'report.performa.salesman',
            'views': [(pivot.id,'pivot')],
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'current'
        }
        return res

    