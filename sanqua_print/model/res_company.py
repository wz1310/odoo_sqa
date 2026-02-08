# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = 'res.company'


    iso_customer_invoice = fields.Char(string='Iso Customer Invoice')
    iso_customer_payment = fields.Char(string='Iso Customer Payment')
    iso_supplier_invoice = fields.Char(string='Iso Supplier Invoice')
    iso_supplier_payment = fields.Char(string='Iso Supplier Payment')
    iso_delivery_order = fields.Char(string='Iso Delivery Order')
    iso_purchase_order = fields.Char(string='Iso Purchase Order')
    iso_receive_order = fields.Char(string='Iso Receive Order')
    iso_sales_return = fields.Char(string='Iso Sales Return')
    iso_purchase_return = fields.Char(string='Iso Purchase Return')
    bank_transfer = fields.Char(string="Bank Transfer on Pro-Forma")