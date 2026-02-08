# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import models, fields, _, api
from odoo.tools import float_is_zero
from odoo.tools.misc import format_date
from datetime import date


class ReportAgedReceivable(models.AbstractModel):
    """ Inherit Account Aged Receivable """
    _inherit = "account.aged.receivable"

    @api.model
    def _get_lines(self, options, line_id=None):
        sign = -1.0 if self.env.context.get('aged_balance') else 1.0
        lines = []
        account_types = [self.env.context.get('account_type')]
        context = {'include_nullified_amount': True}
        if line_id and 'partner_' in line_id:
            # we only want to fetch data about this partner because we are expanding a line
            partner_id_str = line_id.split('_')[1]
            if partner_id_str.isnumeric():
                partner_id = self.env['res.partner'].browse(int(partner_id_str))
            else:
                partner_id = False
            context.update(partner_ids=partner_id)
        results, total, amls = self.env['report.account.report_agedpartnerbalance'].with_context(**context)._get_partner_move_lines(account_types, self._context['date_to'], 'posted', 30)
        if self._context.get('views') == 'ringkasan.piutang':
            lines = self._get_lines_ringkasan(lines, results, sign, options, amls)
            # sebelum menampilkan line cek partner dan company
        else:
            comp = []
            my_partner = self._context.get('partner_ids')
            my_company = self.env.company.id
            if my_company != 2 or my_partner != None:
                comp.append(my_company)
                lines = self._get_lines_base(lines, results, sign, options, amls, total, line_id)
                # ketika company berubah, maka partner pada dropdow akan kembali kosong
                options['partner_ids'] = []
        return lines