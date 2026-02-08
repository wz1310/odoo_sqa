# -*- coding: utf-8 -*-

from num2words import num2words
from odoo import api, fields, models, _


class num_AccountInvoice(models.Model):
    _inherit = "account.move"

    text_amount = fields.Char(string="Text Total", required=False, compute="amount_to_words", store=True)

    @api.depends('amount_total')
    def amount_to_words(self):
        print('test')
        for data in self:
            if data.amount_total > 0 :
                if data.company_id.text_amount_language_currency:
                    data.text_amount = num2words(data.amount_total, to='currency',lang=data.company_id.text_amount_language_currency)
            else:
                data.text_amount = ''