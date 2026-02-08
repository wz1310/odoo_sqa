# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

class ETaxInvoiceMergeLine(models.Model):
    _name = 'etax.invoice.merge.line'
    _description = 'Invoice Commercial Line'

    name = fields.Char(string='Label')
    product_id = fields.Many2one('product.product', string='Product')
    account_id = fields.Many2one('account.account', string='Account')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    quantity = fields.Float(string='Quantity')
    product_uom_id = fields.Many2one('uom.uom', string='UoM')
    price_unit = fields.Float(string='Price')
    display_discount = fields.Float(string='Total Disc.')
    discount = fields.Float(string='Disc.')
    tax_ids = fields.Many2many('account.tax', string='Taxes')
    e_tax_invoice_merge_id = fields.Many2one('etax.invoice.merge', string='E-Tax', ondelete='cascade')
    price_subtotal = fields.Float(string='Price Subtotal')
