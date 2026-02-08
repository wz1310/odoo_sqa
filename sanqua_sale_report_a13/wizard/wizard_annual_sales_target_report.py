# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

import base64
from datetime import datetime
from io import BytesIO

_logger = logging.getLogger(__name__)

class AnnualSalesTargetReportWizard(models.TransientModel):
    _name = 'annual.sales.target.report.wizard'
    _description = 'Wizard Annual Sales Target Report'
    YEARS = [(str(num), str(num)) for num in range(2020, (datetime.now().year)+1 )]

    year = fields.Selection(YEARS, string='Periode',required=True)

    def btn_confirm(self):
        tree = self.env.ref('sanqua_sale_report_a13.annual_sales_target_report_tree')
        context = dict(self.env.context or {})
        context.update({'year':self.year})
        self.env['report.annual.sales.target'].with_context(context).init()
        res = {
            'name': "%s" % (_('Target Penjualan Tahunan')),
            'view_mode': 'tree',
            'res_model': 'report.annual.sales.target',
            'views': [(tree.id,'tree')],
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'current'
        }
        return res