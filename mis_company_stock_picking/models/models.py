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

class StockPicks(models.Model):
    _inherit = 'stock.picking'
    cek_akses = fields.Boolean(compute='open_spicks')

    def open_spicks(self):
    	for rec in self:
    		if rec.company_id.id != self.env.company.id and rec.plant_id.id != self.env.company.id and rec.partner_id != self.env.company.id:
    			self.cek_akses = True
    			raise UserError(_('You are not allowed to access ! Please check your company  before.'))
    		else:
    			self.cek_akses = False