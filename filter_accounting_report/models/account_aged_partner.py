# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import models, fields, _, api
from odoo.tools import float_is_zero
from odoo.tools.misc import format_date
from datetime import date


class ReportAgedReceivable(models.AbstractModel):
    """ Inherit Account Aged Receivable """
    _inherit = "account.aged.receivable"

    filter_operating_units = True
    filter_date = {'mode': 'range', 'filter': 'this_month'}

    def _get_columns_name(self, options):
        if self._context.get('views') == 'ringkasan.piutang':
            columns = [
                {},
                {'name': _("Kode"), 'class': '', 'style': 'white-space:nowrap;'},
                {'name': _("Nama Pelanggan"), 'class': '', 'style': 'white-space:nowrap;'},
                {'name': _("Status"), 'class': '', 'style': 'white-space:nowrap;'},
                {'name': _("TOP"), 'class': '', 'style': 'white-space:nowrap;'},
                {'name': _("Rasio Piutang"), 'class': '', 'style': 'white-space:nowrap;'},
                {'name': _("Limit"), 'class': 'number', 'style': 'white-space:nowrap;'},
                {'name': _("Total Piutang"), 'class': 'number', 'style': 'white-space:nowrap;'},
                {'name': _("Belum Jatuh Tempo"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
                {'name': _("OD 1-30"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
                {'name': _("OD 31-60"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
                {'name': _("OD 61-90"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
                {'name': _("OD 91-120"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
                {'name': _("OVD >121"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
                {},
            ]
        else:
            columns = [
                {},
                {'name': _("Inv. Commercial"), 'class': '', 'style': 'white-space:nowrap;'},
                {'name': _("No. SJ"), 'class': '', 'style': 'white-space:nowrap;'},
                {'name': _("Kode"), 'class': '', 'style': 'white-space:nowrap;'},
                {'name': _("Nama Pelanggan"), 'class': '', 'style': 'white-space:nowrap;'},
                {'name': _("Divisi"), 'class': '', 'style': 'white-space:nowrap;'},
                {'name': _("Salesman"), 'class': '', 'style': 'white-space:nowrap;'},
                {'name': _("Tags"), 'class': '', 'style': 'white-space:nowrap;'},
                {'name': _("Penagih"), 'class': '', 'style': 'white-space:nowrap;'},
                {'name': _("TOP"), 'class': '', 'style': 'white-space:nowrap;'},
                {'name': _("Limit Piutang"), 'class': 'number', 'style': 'white-space:nowrap;'},
                {'name': _("Total Piutang"), 'class': 'number', 'style': 'white-space:nowrap;'},
                {'name': _("Invoice Date"), 'class': 'date', 'style': 'white-space:nowrap;'},
                {'name': _("Due Date"), 'class': 'date', 'style': 'white-space:nowrap;'},
                {'name': _("Journal"), 'class': '', 'style': 'text-align:center; white-space:nowrap;'},
                {'name': _("Account"), 'class': '', 'style': 'text-align:center; white-space:nowrap;'},
                {'name': _("Exp. Date"), 'class': 'date', 'style': 'white-space:nowrap;'},
                {'name': _("Belum Jatuh Tempo"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
                {'name': _("OD 1-30"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
                {'name': _("OD 31-60"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
                {'name': _("OD 61-90"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
                {'name': _("OD 91-120"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
                {'name': _("OVD >121"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
                {'name': _("Total"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            ]
        return columns
    
    def _set_context(self, options):
        """add context account filter data"""
        ctx = super(ReportAgedReceivable, self)._set_context(options)
        if options.get('operating_units'):
            ctx['operating_unit_ids'] = [op_unit.get('id') for op_unit in options.get('operating_units') if op_unit.get('selected')]
        return ctx

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
        else:
            lines = self._get_lines_base(lines, results, sign, options, amls, total, line_id)
        return lines

    def _get_lines_ringkasan(self, lines, results, sign, options, amls):
        for values in results:
            name = values['name']
            tags = ''
            top = ''
            if values['partner_id']:
                partner_id = self.env['res.partner'].browse(values['partner_id'])
                # code_partner = partner_id.code
                # if code_partner and type(code_partner) == type('string'):
                #     name = '[ ' + str(code_partner) + ' ] ' + values['name']
                if partner_id.category_id:
                    # name += ', Status : ' + str(partner_id.category_id[0].name)
                    tags += str(partner_id.category_id[0].name)
                if partner_id and partner_id.partner_pricelist_ids:
                    top = partner_id.partner_pricelist_ids[0].payment_term_id.name
            vals = {
                'id': 'partner_%s' % (values['partner_id'],),
                'name': name,
                'level': 2,
                'columns': [{'name': ''}] * 3 + [{'name': top}] + [{'name': ''}] * 3 + [{'name': self.format_value(sign * v), 'no_format': sign * v}
                                                 for v in [values['direction'], values['4'],
                                                           values['3'], values['2'],
                                                           values['1'], values['0']]],
                'trust': values['trust'],
                'unfoldable': True,
                'unfolded': 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'),
                'partner_id': values['partner_id'],
            }
            lines.append(vals)
            if 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'):
                for line in amls[values['partner_id']]:
                    aml = line['line']
                    salesman = ''
                    kode = ''
                    divisi = ''
                    collector = ''
                    top = ''
                    rasio_piutang = ''
                    limit_piutang = ''
                    total_piutang = ''
                    no_sj = ''
                    nama_pelanggan = ''
                    invoice_commercial = ''

                    
                    if aml.move_id and aml.move_id.commercial_ids:
                        commercial_inv_ids = aml.move_id.commercial_ids.filtered(lambda x:x.state != 'cancel')
                        for data_commercial in commercial_inv_ids:
                            if data_commercial.state == 'draft':
                                invoice_commercial += 'DRAFT'
                            else:
                                invoice_commercial += data_commercial.name

                    if aml.move_id.is_purchase_document():
                        caret_type = 'account.invoice.in'
                    elif aml.move_id.is_sale_document():
                        caret_type = 'account.invoice.out'
                    elif aml.payment_id:
                        caret_type = 'account.payment'
                    else:
                        caret_type = 'account.move'

                    if aml.move_id and aml.move_id.partner_id:
                        nama_pelanggan = aml.move_id.partner_id.name

                    if aml.move_id and aml.move_id.invoice_user_id:
                        salesman = aml.move_id.invoice_user_id.name
                    
                    if aml.move_id and aml.move_id.team_id:
                        divisi = aml.move_id.team_id.name

                    if aml.move_id and aml.move_id.partner_id.code:
                        kode = aml.move_id.partner_id.code
                    if aml.move_id:
                        picking_id = self.env['stock.picking'].search([('invoice_id', '=', aml.move_id.id)])
                        if picking_id:
                            for this in picking_id:
                                no_sj = this.doc_name
                    if aml.move_id and aml.move_id.partner_id.category_id:
                        tags = aml.move_id.partner_id.category_id[0].name

                    #need improve search function to always get from invoice
                    collection_activity_line_id = self.env['collection.activity.line'].search([('invoice_id', '=', aml.move_id.id)], limit = 1)
                    if collection_activity_line_id:
                        if collection_activity_line_id.activity_id and collection_activity_line_id.activity_id.collector_id:
                            collector = collection_activity_line_id.activity_id.collector_id.name
                    if aml.move_id and aml.move_id.invoice_payment_term_id:
                        top = aml.move_id.invoice_payment_term_id.name
                    
                    if aml.move_id.partner_id and aml.move_id.team_id:
                        partner_pricelist_id = self.env['partner.pricelist'].search([('partner_id', '=', aml.move_id.partner_id.id),
                                                                                     ('team_id', '=', aml.move_id.team_id.id)], limit = 1)
                        if partner_pricelist_id:
                            limit_piutang = self.format_value(sign * partner_pricelist_id.credit_limit)
                    if aml.move_id.partner_id:
                        total_due = aml.move_id.partner_id.total_due
                        total_piutang = self.format_value(sign * total_due)
                        
                        if total_due > 0 and self._get_total_omzet():
                            rasio_piutang_vals = total_due / self._get_total_omzet() * 100
                            rasio_piutang = float("{:.5f}".format(rasio_piutang_vals))

                    line_date = aml.date_maturity or aml.date
                    if not self._context.get('no_format'):
                        line_date = format_date(self.env, line_date)
                    vals = {
                        'id': aml.id,
                        'name': aml.move_id.name,
                        'class': 'top-vertical-align', # SanQua
                        'caret_options': caret_type,
                        'level': 4,
                        'parent_id': 'partner_%s' % (values['partner_id'],),
                        'columns': [{'name': v} for v in [kode, nama_pelanggan,tags, top, rasio_piutang, limit_piutang, total_piutang]] +
                                   [{'name': self.format_value(sign * v, blank_if_zero=True), 'no_format': sign * v} for v in [line['period'] == 6-i and line['amount'] or 0 for i in range(7)]],
                        'action_context': {
                            'default_type': aml.move_id.type,
                            'default_journal_id': aml.move_id.journal_id.id,
                        },
                        'title_hover': self._format_aml_name(aml.name, aml.ref, aml.move_id.name),
                    }
                    lines.append(vals)
        return lines

    def _get_lines_base(self, lines, results, sign, options, amls, total, line_id):
        for values in results:
            name = values['name']
            tags = ''
            top = ''
            if values['partner_id']:
                partner_id = self.env['res.partner'].browse(values['partner_id'])
                # code_partner = partner_id.code
                # if code_partner and type(code_partner) == type('string'):
                #     name = '[ ' + str(code_partner) + ' ] ' + values['name']
                if partner_id.category_id:
                    name += ', Status : ' + str(partner_id.category_id[0].name)
                    tags += str(partner_id.category_id[0].name)
                if partner_id and partner_id.partner_pricelist_ids:
                    top = partner_id.partner_pricelist_ids[0].payment_term_id.name
            vals = {
                'id': 'partner_%s' % (values['partner_id'],),
                'name': name,
                'level': 2,
                'columns': [{'name': ''}] * 8 + [{'name': top}] + [{'name': ''}] * 7 + [{'name': self.format_value(sign * v), 'no_format': sign * v}
                                                 for v in [values['direction'], values['4'],
                                                           values['3'], values['2'],
                                                           values['1'], values['0'], values['total']]],
                'trust': values['trust'],
                'unfoldable': True,
                'unfolded': 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'),
                'partner_id': values['partner_id'],
            }
            lines.append(vals)
            if 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'):
                for line in amls[values['partner_id']]:
                    aml = line['line']
                    salesman = ''
                    kode = ''
                    divisi = ''
                    collector = ''
                    top = ''
                    limit_piutang = ''
                    total_piutang = ''
                    no_sj = ''
                    nama_pelanggan = ''
                    invoice_commercial = ''

                    
                    if aml.move_id and aml.move_id.commercial_ids:
                        commercial_inv_ids = aml.move_id.commercial_ids.filtered(lambda x:x.state != 'cancel')
                        for data_commercial in commercial_inv_ids:
                            if data_commercial.state == 'draft':
                                invoice_commercial += 'DRAFT'
                            else:
                                invoice_commercial += data_commercial.name

                    if aml.move_id.is_purchase_document():
                        caret_type = 'account.invoice.in'
                    elif aml.move_id.is_sale_document():
                        caret_type = 'account.invoice.out'
                    elif aml.payment_id:
                        caret_type = 'account.payment'
                    else:
                        caret_type = 'account.move'

                    if aml.move_id and aml.move_id.partner_id:
                        nama_pelanggan = aml.move_id.partner_id.name

                    if aml.move_id and aml.move_id.invoice_user_id:
                        salesman = aml.move_id.invoice_user_id.name
                    
                    if aml.move_id and aml.move_id.team_id:
                        divisi = aml.move_id.team_id.name

                    if aml.move_id and aml.move_id.partner_id.code:
                        kode = aml.move_id.partner_id.code
                    if aml.move_id:
                        picking_id = self.env['stock.picking'].search([('invoice_id', '=', aml.move_id.id)])
                        if picking_id:
                            for this in picking_id:
                                no_sj = this.doc_name
                    # if aml.move_id and aml.move_id.partner_id.category_id:
                    #     tags = aml.move_id.partner_id.category_id

                    #need improve search function to always get from invoice
                    collection_activity_line_id = self.env['collection.activity.line'].search([('invoice_id', '=', aml.move_id.id)], limit = 1)
                    if collection_activity_line_id:
                        if collection_activity_line_id.activity_id and collection_activity_line_id.activity_id.collector_id:
                            collector = collection_activity_line_id.activity_id.collector_id.name
                    if aml.move_id and aml.move_id.invoice_payment_term_id:
                        top = aml.move_id.invoice_payment_term_id.name
                    
                    if aml.move_id.partner_id and aml.move_id.team_id:
                        partner_pricelist_id = self.env['partner.pricelist'].search([('partner_id', '=', aml.move_id.partner_id.id),
                                                                                     ('team_id', '=', aml.move_id.team_id.id)], limit = 1)
                        if partner_pricelist_id:
                            limit_piutang = self.format_value(sign * partner_pricelist_id.credit_limit)
                    if aml.move_id.partner_id:
                        total_piutang = self.format_value(sign * aml.move_id.partner_id.total_due)

                    line_date = aml.date_maturity or aml.date
                    if not self._context.get('no_format'):
                        line_date = format_date(self.env, line_date)
                    vals = {
                        'id': aml.id,
                        'name': aml.move_id.name,
                        'class': 'top-vertical-align', # SanQua
                        'caret_options': caret_type,
                        'level': 4,
                        'parent_id': 'partner_%s' % (values['partner_id'],),
                        'columns': [{'name': v} for v in [invoice_commercial, no_sj, kode, nama_pelanggan, divisi, salesman, tags, collector, top, limit_piutang, total_piutang, format_date(self.env, aml.move_id.invoice_date), format_date(self.env, aml.date_maturity or aml.date), aml.journal_id.code, aml.account_id.display_name, format_date(self.env, aml.expected_pay_date)]] +
                                   [{'name': self.format_value(sign * v, blank_if_zero=True), 'no_format': sign * v} for v in [line['period'] == 6-i and line['amount'] or 0 for i in range(7)]],
                        'action_context': {
                            'default_type': aml.move_id.type,
                            'default_journal_id': aml.move_id.journal_id.id,
                        },
                        'title_hover': self._format_aml_name(aml.name, aml.ref, aml.move_id.name),
                    }
                    lines.append(vals)
        if total and not line_id:
            total_line = {
                'id': 0,
                'name': _('Total'),
                'class': 'total',
                'level': 2,
                'columns': [{'name': ''}] * 16 + [{'name': self.format_value(sign * v), 'no_format': sign * v} for v in [total[6], total[4], total[3], total[2], total[1], total[0], total[5]]],
            }
            lines.append(total_line)
        return lines

    def _get_total_omzet(self):
        query = """
            SELECT 
                sum(amount_total) 
            FROM 
                sale_order 
            WHERE
                    company_id = 2 
                AND 
                    state in ('sale','done') 
                AND 
                    EXTRACT('MONTH' from date_order) = '%s' 
                AND 
                    EXTRACT('YEAR' from date_order) = '%s';
        """
        self._cr.execute(query, (date.today().month,date.today().year,))
        res = self._cr.dictfetchone()
        return res.get('sum')
        
class ReportAgedPayable(models.AbstractModel):
    """ Inherit Account Aged Payable """
    _inherit = "account.aged.payable"

    filter_operating_units = True
    filter_date = {'mode': 'range', 'filter': 'this_month'}

    def _set_context(self, options):
        """add context account filter data"""
        ctx = super(ReportAgedPayable, self)._set_context(options)
        if options.get('operating_units'):
            ctx['operating_unit_ids'] = [op_unit.get('id') for op_unit in options.get('operating_units') if op_unit.get('selected')]
        return ctx
    
    def _get_columns_name(self, options):
        columns = [
            {},
            {'name': _("Nama Vendor"), 'class': '', 'style': 'white-space:nowrap;'},
            {'name': _("No. Inv Vendor"), 'class': '', 'style': 'white-space:nowrap;'},
            {'name': _("Tgl. Jatuh Tempo"), 'class': 'date', 'style': 'white-space:nowrap;'},
            {'name': _("Bill Date"), 'class': 'date', 'style': 'white-space:nowrap;'},
            {'name': _("Accounting Date"), 'class': 'date', 'style': 'white-space:nowrap;'},
            {'name': _("Journal"), 'class': '', 'style': 'text-align:center; white-space:nowrap;'},
            {'name': _("Account"), 'class': '', 'style': 'text-align:center; white-space:nowrap;'},
            # {'name': _("Exp. Date"), 'class': 'date', 'style': 'white-space:nowrap;'},
            {'name': _("Belum jatuh tempo"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            {'name': _("OD 1-30"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            {'name': _("OD 31-60"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            {'name': _("OD 61-90"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            {'name': _("OD 91 - 120"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            {'name': _("> 120"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            {'name': _("Total"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
        ]
        return columns

    @api.model
    def _get_lines(self, options, line_id=None):
        sign = -1.0 if self.env.context.get('aged_balance') else 1.0
        lines = []
        account_types = [self.env.context.get('account_type')]
        context = {'include_nullified_amount': True}
        if line_id and 'partner_' in line_id:
            # we only want to fetch data about this partner because we are expanding a line
            context.update(partner_ids=self.env['res.partner'].browse(int(line_id.split('_')[1])))
        results, total, amls = self.env['report.account.report_agedpartnerbalance'].with_context(**context)._get_partner_move_lines(account_types, self._context['date_to'], 'posted', 30)

        for values in results:
            vals = {
                'id': 'partner_%s' % (values['partner_id'],),
                'name': values['name'],
                'level': 2,
                'columns': [{'name': ''}] * 7 + [{'name': self.format_value(sign * v), 'no_format': sign * v}
                                                 for v in [values['direction'], values['4'],
                                                           values['3'], values['2'],
                                                           values['1'], values['0'], values['total']]],
                'trust': values['trust'],
                'unfoldable': True,
                'unfolded': 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'),
                'partner_id': values['partner_id'],
            }
            lines.append(vals)
            if 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'):
                for line in amls[values['partner_id']]:
                    aml = line['line']
                    if aml.move_id.is_purchase_document():
                        caret_type = 'account.invoice.in'
                    elif aml.move_id.is_sale_document():
                        caret_type = 'account.invoice.out'
                    elif aml.payment_id:
                        caret_type = 'account.payment'
                    else:
                        caret_type = 'account.move'

                    nama_pelanggan = ''
                    if aml.move_id and aml.move_id.partner_id:
                        nama_pelanggan = aml.move_id.partner_id.name

                    line_date = aml.date_maturity or aml.date
                    if not self._context.get('no_format'):
                        line_date = format_date(self.env, line_date)
                    vals = {
                        'id': aml.id,
                        'name': aml.move_id.name,
                        'class': 'top-vertical-align', # SanQua
                        'caret_options': caret_type,
                        'level': 4,
                        'parent_id': 'partner_%s' % (values['partner_id'],),
                        'columns': [{'name': v} for v in [nama_pelanggan, aml.move_id.ref,format_date(self.env, aml.date_maturity or aml.date), format_date(self.env, aml.move_id.invoice_date), format_date(self.env, aml.move_id.date), aml.journal_id.code, aml.account_id.display_name]] +
                                   [{'name': self.format_value(sign * v, blank_if_zero=True), 'no_format': sign * v} for v in [line['period'] == 6-i and line['amount'] or 0 for i in range(7)]],
                        'action_context': {
                            'default_type': aml.move_id.type,
                            'default_journal_id': aml.move_id.journal_id.id,
                        },
                        'title_hover': self._format_aml_name(aml.name, aml.ref, aml.move_id.name),
                    }
                    lines.append(vals)
        if total and not line_id:
            total_line = {
                'id': 0,
                'name': _('Total'),
                'class': 'total',
                'level': 2,
                'columns': [{'name': ''}] * 7 + [{'name': self.format_value(sign * v), 'no_format': sign * v} for v in [total[6], total[4], total[3], total[2], total[1], total[0], total[5]]],
            }
            lines.append(total_line)
        return lines

class ReportAgedPartnerBalance(models.AbstractModel):
    """ Inherit Report Aged Partner Balnace """
    _inherit = 'report.account.report_agedpartnerbalance'

    def _get_partner_move_lines(self, account_type, date_from, target_move, period_length):
        """ Replace function to filter Journal Items with selected Operation Units """
        ctx = self._context
        if ctx.get('operating_unit_ids'):
            # Set filter Journal based on Operating Units
            journal_ids = self.env.user.journal_ids
            journal_ids_only_in_operating_unit = []
            empty_journal = None
            if ctx.get('operating_unit_ids'):
                journal_ids_only_in_operating_unit = journal_ids.filtered(lambda l:l.branch_id.id in tuple(ctx['operating_unit_ids'])).ids
                if not journal_ids_only_in_operating_unit:
                    journal_ids_only_in_operating_unit = [empty_journal]
            filter_journal_ids = tuple(journal_ids_only_in_operating_unit if ctx.get('operating_unit_ids') else journal_ids.ids)

            periods = {}
            date_from = fields.Date.from_string(date_from)
            start = date_from
            for i in range(5)[::-1]:
                stop = start - relativedelta(days=period_length)
                period_name = str((5-(i+1)) * period_length + 1) + '-' + str((5-i) * period_length)
                period_stop = (start - relativedelta(days=1)).strftime('%Y-%m-%d')
                if i == 0:
                    period_name = '+' + str(4 * period_length)
                periods[str(i)] = {
                    'name': period_name,
                    'stop': period_stop,
                    'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
                }
                start = stop

            res = []
            total = []
            partner_clause = ''
            cr = self.env.cr
            user_company = self.env.company
            user_currency = user_company.currency_id
            company_ids = self._context.get('company_ids') or [user_company.id]
            move_state = ['draft', 'posted']
            if target_move == 'posted':
                move_state = ['posted']
            arg_list = (tuple(move_state), tuple(account_type), date_from, date_from,)
            if ctx.get('partner_ids'):
                partner_clause = 'AND (l.partner_id IN %s)'
                arg_list += (tuple(ctx['partner_ids'].ids),)
            if ctx.get('partner_categories'):
                partner_clause += 'AND (l.partner_id IN %s)'
                partner_ids = self.env['res.partner'].search([('category_id', 'in', ctx['partner_categories'].ids)]).ids
                arg_list += (tuple(partner_ids or [0]),)
            # Add journal filter here
            arg_list += (date_from, tuple(company_ids), filter_journal_ids)            

            query = '''
                SELECT DISTINCT l.partner_id, res_partner.name AS name, UPPER(res_partner.name) AS UPNAME, CASE WHEN prop.value_text IS NULL THEN 'normal' ELSE prop.value_text END AS trust
                FROM account_move_line AS l
                  LEFT JOIN res_partner ON l.partner_id = res_partner.id
                  LEFT JOIN ir_property prop ON (prop.res_id = 'res.partner,'||res_partner.id AND prop.name='trust' AND prop.company_id=%s),
                  account_account, account_move am
                WHERE (l.account_id = account_account.id)
                    AND (l.move_id = am.id)
                    AND (am.state IN %s)
                    AND (account_account.internal_type IN %s)
                    AND (
                            l.reconciled IS FALSE
                            OR l.id IN(
                                SELECT credit_move_id FROM account_partial_reconcile where max_date > %s
                                UNION ALL
                                SELECT debit_move_id FROM account_partial_reconcile where max_date > %s
                            )
                        )
                        ''' + partner_clause + '''
                    AND (l.date <= %s)
                    AND l.company_id IN %s
                    AND l.journal_id IN %s
                ORDER BY UPPER(res_partner.name)'''
            arg_list = (self.env.company.id,) + arg_list
            cr.execute(query, arg_list)

            partners = cr.dictfetchall()
            # put a total of 0
            for i in range(7):
                total.append(0)

            # Build a string like (1,2,3) for easy use in SQL query
            partner_ids = [partner['partner_id'] for partner in partners if partner['partner_id']]
            lines = dict((partner['partner_id'] or False, []) for partner in partners)
            if not partner_ids:
                return [], [], {}

            # Use one query per period and store results in history (a list variable)
            # Each history will contain: history[1] = {'<partner_id>': <partner_debit-credit>}
            history = []
            for i in range(5):
                args_list = (tuple(move_state), tuple(account_type), tuple(partner_ids),)
                dates_query = '(COALESCE(l.date_maturity,l.date)'

                if periods[str(i)]['start'] and periods[str(i)]['stop']:
                    dates_query += ' BETWEEN %s AND %s)'
                    args_list += (periods[str(i)]['start'], periods[str(i)]['stop'])
                elif periods[str(i)]['start']:
                    dates_query += ' >= %s)'
                    args_list += (periods[str(i)]['start'],)
                else:
                    dates_query += ' <= %s)'
                    args_list += (periods[str(i)]['stop'],)
                # Add journal filter here
                args_list += (date_from, tuple(company_ids), filter_journal_ids)

                query = '''SELECT l.id
                        FROM account_move_line AS l, account_account, account_move am
                        WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                            AND (am.state IN %s)
                            AND (account_account.internal_type IN %s)
                            AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                            AND ''' + dates_query + '''
                        AND (l.date <= %s)
                        AND l.company_id IN %s
                        AND l.journal_id IN %s
                        ORDER BY COALESCE(l.date_maturity, l.date)'''
                cr.execute(query, args_list)
                partners_amount = {}
                aml_ids = cr.fetchall()
                aml_ids = aml_ids and [x[0] for x in aml_ids] or []
                for line in self.env['account.move.line'].browse(aml_ids).with_context(prefetch_fields=False):
                    partner_id = line.partner_id.id or False
                    if partner_id not in partners_amount:
                        partners_amount[partner_id] = 0.0
                    line_amount = line.company_id.currency_id._convert(line.balance, user_currency, user_company, date_from)
                    if user_currency.is_zero(line_amount):
                        continue
                    for partial_line in line.matched_debit_ids:
                        if partial_line.max_date <= date_from:
                            line_amount += partial_line.company_id.currency_id._convert(partial_line.amount, user_currency, user_company, date_from)
                    for partial_line in line.matched_credit_ids:
                        if partial_line.max_date <= date_from:
                            line_amount -= partial_line.company_id.currency_id._convert(partial_line.amount, user_currency, user_company, date_from)

                    if not self.env.company.currency_id.is_zero(line_amount):
                        partners_amount[partner_id] += line_amount
                        lines.setdefault(partner_id, [])
                        lines[partner_id].append({
                            'line': line,
                            'amount': line_amount,
                            'period': i + 1,
                            })
                history.append(partners_amount)

            # This dictionary will store the not due amount of all partners
            undue_amounts = {}
            query = '''SELECT l.id
                    FROM account_move_line AS l, account_account, account_move am
                    WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                        AND (am.state IN %s)
                        AND (account_account.internal_type IN %s)
                        AND (COALESCE(l.date_maturity,l.date) >= %s)\
                        AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                    AND (l.date <= %s)
                    AND l.company_id IN %s
                    AND l.journal_id IN %s
                    ORDER BY COALESCE(l.date_maturity, l.date)'''
            # Add journal filter here
            cr.execute(query, (tuple(move_state), tuple(account_type), date_from, tuple(partner_ids), date_from, tuple(company_ids), filter_journal_ids))
            aml_ids = cr.fetchall()
            aml_ids = aml_ids and [x[0] for x in aml_ids] or []
            for line in self.env['account.move.line'].browse(aml_ids):
                partner_id = line.partner_id.id or False
                if partner_id not in undue_amounts:
                    undue_amounts[partner_id] = 0.0
                line_amount = line.company_id.currency_id._convert(line.balance, user_currency, user_company, date_from)
                if user_currency.is_zero(line_amount):
                    continue
                for partial_line in line.matched_debit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount += partial_line.company_id.currency_id._convert(partial_line.amount, user_currency, user_company, date_from)
                for partial_line in line.matched_credit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount -= partial_line.company_id.currency_id._convert(partial_line.amount, user_currency, user_company, date_from)
                if not self.env.company.currency_id.is_zero(line_amount):
                    undue_amounts[partner_id] += line_amount
                    lines.setdefault(partner_id, [])
                    lines[partner_id].append({
                        'line': line,
                        'amount': line_amount,
                        'period': 6,
                    })

            for partner in partners:
                if partner['partner_id'] is None:
                    partner['partner_id'] = False
                at_least_one_amount = False
                values = {}
                undue_amt = 0.0
                if partner['partner_id'] in undue_amounts:  # Making sure this partner actually was found by the query
                    undue_amt = undue_amounts[partner['partner_id']]

                total[6] = total[6] + undue_amt
                values['direction'] = undue_amt
                if not float_is_zero(values['direction'], precision_rounding=self.env.company.currency_id.rounding):
                    at_least_one_amount = True

                for i in range(5):
                    during = False
                    if partner['partner_id'] in history[i]:
                        during = [history[i][partner['partner_id']]]
                    # Adding counter
                    total[(i)] = total[(i)] + (during and during[0] or 0)
                    values[str(i)] = during and during[0] or 0.0
                    if not float_is_zero(values[str(i)], precision_rounding=self.env.company.currency_id.rounding):
                        at_least_one_amount = True
                values['total'] = sum([values['direction']] + [values[str(i)] for i in range(5)])
                # Add for total
                total[(i + 1)] += values['total']
                values['partner_id'] = partner['partner_id']
                if partner['partner_id']:
                    values['name'] = len(partner['name']) >= 45 and partner['name'][0:40] + '...' or partner['name']
                    values['trust'] = partner['trust']
                else:
                    values['name'] = _('Unknown Partner')
                    values['trust'] = False

                if at_least_one_amount or (self._context.get('include_nullified_amount') and lines[partner['partner_id']]):
                    res.append(values)
            return res, total, lines
        else:
            return super(ReportAgedPartnerBalance, self)._get_partner_move_lines(account_type, date_from, target_move, period_length)
