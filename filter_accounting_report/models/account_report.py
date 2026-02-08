# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.misc import format_date, DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta

class AccountReport(models.AbstractModel):
    """ Inherit Account Report """
    _inherit = 'account.report'

    filter_operating_units = None
    filter_warehouse = None

    ##################################
    ## Operating Units
    ##################################

    @api.model
    def _get_filter_operating_unit(self):
        return self.env['res.branch'].search([])

    @api.model
    def _init_filter_operating_units(self, options, previous_options=None):
        if self.filter_operating_units is None:
            return
        prev_operating_units = previous_options and previous_options.get('operating_units') or []
        selected_operating_units = [op_unit['id'] for op_unit in prev_operating_units if op_unit.get('selected')]
        
        options['operating_units'] = []
        operating_unit_read = self._get_filter_operating_unit()
        i = 0
        for c in operating_unit_read:
            if i == 0:
                options['operating_units'].append({'id': 'divider', 'name': self.env.user.company_id.name})
            options['operating_units'].append({
                'id': c.id, 
                'name': c.name, 
                'selected': c.id in selected_operating_units,
            })
            i += 1

    @api.model
    def _get_options_operating_units(self, options):
        operating_units = []
        for op_unit_option in options.get('operating_units', []):
            if op_unit_option['id'] in ('divider', 'group'):
                continue
            if op_unit_option['selected']:
                operating_units.append(op_unit_option)
        return operating_units

    @api.model
    def _get_options_operating_units_domain(self, options):
        if not options.get('operating_units'):
            return []

        selected_operating_units = self._get_options_operating_units(options)
        return selected_operating_units and [('journal_id.branch_id', 'in', [op_unit['id'] for op_unit in selected_operating_units])] or []

    @api.model
    def _get_options_domain(self, options):
        domain = super(AccountReport, self)._get_options_domain(options)
        domain += self._get_options_operating_units_domain(options)
        return domain

    ##################################
    ## Warehouse
    ##################################

    @api.model
    def _get_filter_warehouse(self):
        return self.env['stock.warehouse'].search([('company_id','in',self.env.context['allowed_company_ids'])],order="company_id, name")

    @api.model
    def _init_filter_warehouse(self, options, previous_options=None):
        if self.filter_warehouse is None:
            return
        prev_warehouse = previous_options and previous_options.get('warehouse') or []
        selected_warehouse = [warehouse['id'] for warehouse in prev_warehouse if warehouse.get('selected')]
        
        options['warehouse'] = []
        warehouse_read = self._get_filter_warehouse()
        i = 0
        previous_company = False

        for j in warehouse_read:
            if j.company_id != previous_company:
                options['warehouse'].append({'id': 'divider', 'name': j.company_id.name})
                previous_company = j.company_id
            options['warehouse'].append({
                'id': j.id,
                'name': j.name,
                'selected': j.id in selected_warehouse,
            })
            # if i == 0:
            #     options['warehouse'].append({'id': 'divider', 'name': self.env.user.company_id.name})
            #     print("")
            # options['warehouse'].append({
            #     'id': c.id, 
            #     'name': c.name, 
            #     'selected': c.id in selected_warehouse,
            # })
            # i += 1

    @api.model
    def _get_options_warehouse(self, options):
        warehouse = []
        for warehouse_option in options.get('warehouse', []):
            if warehouse_option['id'] in ('divider', 'group'):
                continue
            if warehouse_option['selected']:
                warehouse.append(warehouse_option)
        return warehouse

    @api.model
    def _get_options_warehouse_domain(self, options):
        if not options.get('warehouse'):
            return []

        selected_warehouse = self._get_options_warehouse(options)
        return selected_warehouse and [('journal_id.branch_id', 'in', [warehouse['id'] for warehouse in selected_warehouse])] or []

    @api.model
    def _get_options_domain(self, options):
        domain = super(AccountReport, self)._get_options_domain(options)
        domain += self._get_options_warehouse_domain(options)
        return domain

        # //////////////////////////////////////////////////////////////////////////


class ReportPartnerLedger(models.AbstractModel):
    '''inherit account.partner.ledger'''
    _inherit = "account.partner.ledger"

    filter_operating_units = True


class ReportAccountFinancialReport(models.Model):
    _inherit = "account.financial.html.report"

    filter_operating_units = True

    def _set_context(self, options):
        ctx = super(ReportAccountFinancialReport, self)._set_context(options)
        if options.get('operating_units'):
            ctx['operating_unit_ids'] = [op_unit.get('id') for op_unit in options.get('operating_units') if op_unit.get('selected')]
        return ctx


class ReportAccountGeneralLedger(models.AbstractModel):
    '''inherit account.general.ledger'''
    _inherit = "account.general.ledger"

    filter_operating_units = True

    @api.model
    def _get_columns_name(self, options):
        return [
            {'name': ''},
            {'name': _('Date'), 'class': 'date'},
            {'name': _('Communication')},
            {'name': _('Analytic_Account')},
            {'name': _('Partner')},
            {'name': _('Currency'), 'class': 'number'},
            {'name': _('Debit'), 'class': 'number'},
            {'name': _('Credit'), 'class': 'number'},
            {'name': _('Balance'), 'class': 'number'}
        ]

    @api.model
    def _get_query_amls(self, options, expanded_account, offset=None, limit=None):
        ''' Construct a query retrieving the account.move.lines when expanding a report line with or without the load
        more.
        :param options:             The report options.
        :param expanded_account:    The account.account record corresponding to the expanded line.
        :param offset:              The offset of the query (used by the load more).
        :param limit:               The limit of the query (used by the load more).
        :return:                    (query, params)
        '''

        unfold_all = options.get('unfold_all') or (self._context.get('print_mode') and not options['unfolded_lines'])

        # Get sums for the account move lines.
        # period: [('date' <= options['date_to']), ('date', '>=', options['date_from'])]
        if expanded_account:
            domain = [('account_id', '=', expanded_account.id)]
        elif unfold_all:
            domain = []
        elif options['unfolded_lines']:
            domain = [('account_id', 'in', [int(line[8:]) for line in options['unfolded_lines']])]

        new_options = self._force_strict_range(options)
        tables, where_clause, where_params = self._query_get(new_options, domain=domain)
        ct_query = self._get_query_currency_table(options)
        query = '''
            SELECT
                account_move_line.id,
                account_move_line.date,
                account_move_line.date_maturity,
                account_move_line.name,
                account_move_line.ref,
                account_move_line.company_id,
                account_move_line.account_id,
                account_move_line.payment_id,
                aac.code as code_aac,
                aac.name as analytic_account_id,
                account_move_line.partner_id,
                account_move_line.currency_id,
                account_move_line.amount_currency,
                ROUND(account_move_line.debit * currency_table.rate, currency_table.precision)   AS debit,
                ROUND(account_move_line.credit * currency_table.rate, currency_table.precision)  AS credit,
                ROUND(account_move_line.balance * currency_table.rate, currency_table.precision) AS balance,
                account_move_line__move_id.name         AS move_name,
                company.currency_id                     AS company_currency_id,
                partner.name                            AS partner_name,
                account_move_line__move_id.type         AS move_type,
                account.code                            AS account_code,
                account.name                            AS account_name,
                journal.code                            AS journal_code,
                journal.name                            AS journal_name,
                full_rec.name                           AS full_rec_name
            FROM account_move_line
            LEFT JOIN account_move account_move_line__move_id ON account_move_line__move_id.id = account_move_line.move_id
            LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
            LEFT JOIN res_company company               ON company.id = account_move_line.company_id
            LEFT JOIN res_partner partner               ON partner.id = account_move_line.partner_id
            LEFT JOIN account_account account           ON account.id = account_move_line.account_id
            LEFT JOIN account_journal journal           ON journal.id = account_move_line.journal_id
            LEFT JOIN account_full_reconcile full_rec   ON full_rec.id = account_move_line.full_reconcile_id
            LEFT JOIN account_analytic_account aac ON  aac.id = account_move_line.analytic_account_id
            WHERE %s
            ORDER BY account_move_line.id
        ''' % (ct_query, where_clause)

        if offset:
            query += ' OFFSET %s '
            where_params.append(offset)
        if limit:
            query += ' LIMIT %s '
            where_params.append(limit)

        return query, where_params

    @api.model
    def _get_aml_line(self, options, account, aml, cumulated_balance):
        if aml['payment_id']:
            caret_type = 'account.payment'
        elif aml['move_type'] in ('in_refund', 'in_invoice', 'in_receipt'):
            caret_type = 'account.invoice.in'
        elif aml['move_type'] in ('out_refund', 'out_invoice', 'out_receipt'):
            caret_type = 'account.invoice.out'
        else:
            caret_type = 'account.move'

        if aml['ref'] and aml['name']:
            title = '%s - %s' % (aml['name'], aml['ref'])
        elif aml['ref']:
            title = aml['ref']
        elif aml['name']:
            title = aml['name']
        else:
            title = ''
        if aml['currency_id']:
            currency = self.env['res.currency'].browse(aml['currency_id'])
        else:
            currency = False

        analytic_account_id = ''
        if aml['analytic_account_id']:
            analytic_account_id = aml['analytic_account_id']
        
        code_aac = ''
        if aml['code_aac']:
            code_aac = '['+ aml['code_aac'] + '] '

        return {
            'id': aml['id'],
            'caret_options': caret_type,
            'class': 'top-vertical-align',
            'parent_id': 'account_%d' % aml['account_id'],
            'name': aml['move_name'],
            'columns': [
                {'name': format_date(self.env, aml['date']), 'class': 'date'},
                {'name': self._format_aml_name(aml['name'], aml['ref'], aml['move_name']), 'title': title, 'class': 'whitespace_print'},
                {'name': code_aac + analytic_account_id, 'title': title, 'class': 'whitespace_print'},
                {'name': aml['partner_name'], 'title': aml['partner_name'], 'class': 'whitespace_print'},
                {'name': currency and self.format_value(aml['amount_currency'], currency=currency, blank_if_zero=True) or '', 'class': 'number'},
                {'name': self.format_value(aml['debit'], blank_if_zero=True), 'class': 'number'},
                {'name': self.format_value(aml['credit'], blank_if_zero=True), 'class': 'number'},
                {'name': self.format_value(cumulated_balance), 'class': 'number'},
            ],
            'level': 4,
        }
