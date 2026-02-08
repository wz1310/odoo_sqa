# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.tools.misc import formatLang, format_date, get_lang

from datetime import date, timedelta
from itertools import groupby
from itertools import zip_longest
from hashlib import sha256
from json import dumps


class dn_AccountMove(models.Model):
    _inherit = "account.move"

    state_check = fields.Selection([('not_checked', 'Not Checked'), ('checked', 'Checked')], 'State of checked', required=True, default='not_checked'
                                    , readonly=True,states={'draft': [('readonly', False)]})

    @api.model
    def write(self, vals):
        
        account_move = super(dn_AccountMove, self).write(vals)
        new_date = vals.get('date_start') or self.date    
        for line in self.line_ids:
            # print(line.id,' bb tes')
            # print(new_date,' date line')
            line.sudo().write({
                'date' : new_date
                })
        return account_move




    