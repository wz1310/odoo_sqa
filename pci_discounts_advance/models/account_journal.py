# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
import re


class AccountJournal(models.Model):
    _inherit = "account.journal"


    discount_account_id = fields.Many2one('account.account','Discount Account')