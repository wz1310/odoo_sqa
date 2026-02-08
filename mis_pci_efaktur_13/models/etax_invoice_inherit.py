# -*- coding: utf-8 -*-
"""E-Faktur object, inherit etax.invoice"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError

class ETaxInvoice(models.Model):
    _inherit = 'etax.invoice'

    @api.depends('invoice_id','is_replaced_e_tax','name')
    def _compute_tax_number(self):
        print(">>> Call inherited function <_compute_tax_number>")
        for rec in self:
            digit = rec.tax_digit or ''
            name =  rec.name or ''

            # PCI Version
            # rec.tax_number = digit + str(int(rec.is_replaced_e_tax))+'.' + name

            # SanQua Version
            rec.tax_number = '0.' + name[1:16]
            # return super(ETaxInvoice,self)._compute_tax_number()