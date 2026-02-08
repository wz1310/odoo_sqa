# -*- coding: utf-8 -*-

from num2words import num2words
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class dn_ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    def name_get(self):
        result = []
        for dt in self:
            name = dt.acc_number + ' (' + dt.bank_id.name+ ')'
            result.append((dt.id, name))
        return result