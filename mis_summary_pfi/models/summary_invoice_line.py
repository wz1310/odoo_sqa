# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

class SummaryInvoiceLine(models.Model):
    _name = 'summary.invoice.line'
    _description = 'PFI Summary invoice line'

    name = fields.Char(string='Label')
    product_id = fields.Many2one('product.product', string='Product')
    account_id = fields.Many2one('account.account', string='Account')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    quantity = fields.Float(string='Quantity')
    product_uom_id = fields.Many2one('uom.uom', string='UoM')
    price_unit = fields.Float(string='Price')
    discount_fixed_line = fields.Float(string='Discount (Rp)/qty',readonly=False)
    discount = fields.Float(string='Disc (%)')
    tax_ids = fields.Many2many('account.tax', string='Taxes')
    price_subtotal = fields.Float(string='Price Subtotal')
    hide_zero_price = fields.Boolean(string='Hide zero price', store=True)
    move_id = fields.Many2one('account.move', string='Account Move', ondelete='cascade', index=True)