# -*- coding: utf-8 -*-
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import UserError,ValidationError,RedirectWarning,AccessError

import logging
_logger = logging.getLogger(__name__)

import xml.etree as etr
import xml.etree.ElementTree as ET
from ast import literal_eval
import re

import datetime

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    test_column_1 = fields.Many2one('res.company')
    my_domain_id = fields.One2many('product.product','id',compute='cek_dom')
    cek_akses = fields.Boolean(compute='open_so')


    @api.onchange('order_line')
    def onc_mydom(self):
        my_ids = self.order_line.mapped('product_id')
        self.my_domain_id = my_ids

    def cek_dom(self):
    	my_ids = self.order_line.mapped('product_id')
    	for rec in self:
    		if self.order_line:
    			rec.my_domain_id = my_ids
    		else:
    			rec.my_domain_id = False

    def open_so(self):
    	for rec in self:
    		if rec.company_id.id != self.env.company.id and rec.plant_id.id != self.env.company.id:
    			self.cek_akses = True
    			raise UserError(_('You are not allowed to access ! Please check your company  before.'))
    		else:
    			self.cek_akses = False