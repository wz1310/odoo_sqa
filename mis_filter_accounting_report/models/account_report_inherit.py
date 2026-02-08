# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.misc import format_date, DEFAULT_SERVER_DATE_FORMAT

class ReportAccountGeneralLedger(models.AbstractModel):
    _inherit = "account.general.ledger"

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
                # PCI Version
                # {'name': format_date(self.env, aml['date']), 'class': 'date'},
                # SanQua version: takeout the format_date
                {'name': aml['date'], 'class': 'date'},
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

class ReportAccountInherits(models.AbstractModel):
    _inherit = "account.report"

    @api.model
    def _init_filter_analytic(self, options, previous_options=None):
        res = super(ReportAccountInherits, self)._init_filter_analytic(options, previous_options)

        if self.user_has_groups('analytic.group_analytic_accounting'):
            options['analytic_account_group'] = previous_options and previous_options.get('analytic_account_group') or []
            analytic_account_group_ids = [int(accg) for accg in options['analytic_account_group']]
            selected_analytic_accounts_group = analytic_account_group_ids \
                                         and self.env['account.analytic.group'].browse(analytic_account_group_ids) \
                                         or self.env['account.analytic.group']
            options['selected_analytic_account_group_names'] = selected_analytic_accounts_group.mapped('name')
        return res

    @api.model
    def _get_options_analytic_domain(self, options):
        super(ReportAccountInherits, self)._get_options_analytic_domain(options)
        domain = []
        if options.get('analytic_account_group'):
            analytic_account_group_ids = [int(accg) for accg in options['analytic_account_group']]
            domain.append(('analytic_account_id.group_id', 'in', analytic_account_group_ids))
            
        if options.get('analytic_accounts'):
            print("ANL ACCOUNT", options.get('analytic_accounts'))
            analytic_account_ids = [int(acc) for acc in options['analytic_accounts']]
            domain.append(('analytic_account_id', 'in', analytic_account_ids))

        if options.get('analytic_tags'):
            print("ANL TAGS", options.get('analytic_tags'))
            analytic_tag_ids = [int(tag) for tag in options['analytic_tags']]
            domain.append(('analytic_tag_ids', 'in', analytic_tag_ids))
        return domain

class ReportAccountInheritss(models.Model):
    _inherit = "account.financial.html.report"

    def _set_context(self, options):
        """This method will set information inside the context based on the options dict as some options need to be in context for the query_get method defined in account_move_line"""
        ctx = self.env.context.copy()
        if options.get('date') and options['date'].get('date_from'):
            ctx['date_from'] = options['date']['date_from']
        if options.get('date'):
            ctx['date_to'] = options['date'].get('date_to') or options['date'].get('date')
        if options.get('all_entries') is not None:
            ctx['state'] = options.get('all_entries') and 'all' or 'posted'
        if options.get('journals'):
            ctx['journal_ids'] = [j.get('id') for j in options.get('journals') if j.get('selected')]
        company_ids = []
        if options.get('multi_company'):
            company_ids = [c.get('id') for c in options['multi_company'] if c.get('selected')]
            company_ids = company_ids if len(company_ids) > 0 else [c.get('id') for c in options['multi_company']]
        ctx['company_ids'] = len(company_ids) > 0 and company_ids or [self.env.company.id]
        if options.get('analytic_accounts'):
            ctx['analytic_account_ids'] = self.env['account.analytic.account'].browse([int(acc) for acc in options['analytic_accounts']])
        if options.get('analytic_account_group'):
            ctx['analytic_account_group_ids'] = self.env['account.analytic.group'].browse([int(accg) for accg in options['analytic_account_group']])
        if options.get('analytic_tags'):
            ctx['analytic_tag_ids'] = self.env['account.analytic.tag'].browse([int(t) for t in options['analytic_tags']])
        if options.get('partner_ids'):
            ctx['partner_ids'] = self.env['res.partner'].browse([int(partner) for partner in options['partner_ids']])
        if options.get('partner_categories'):
            ctx['partner_categories'] = self.env['res.partner.category'].browse([int(category) for category in options['partner_categories']])
        return ctx

class AccountMoveLineInherit(models.Model):
    """inherit model Account Move Line"""
    _inherit = 'account.move.line'

    @api.model
    def _query_get(self, domain=None):
        super(AccountMoveLineInherit, self)._query_get(domain)
        self.check_access_rights('read')
        context = dict(self._context or {})
        domain = domain or []
        if not isinstance(domain, (list, tuple)):
            domain = safe_eval(domain)

        date_field = 'date'
        if context.get('aged_balance'):
            date_field = 'date_maturity'
        if context.get('date_to'):
            domain += [(date_field, '<=', context['date_to'])]
        if context.get('date_from'):
            if not context.get('strict_range'):
                domain += ['|', (date_field, '>=', context['date_from']), ('account_id.user_type_id.include_initial_balance', '=', True)]
            elif context.get('initial_bal'):
                domain += [(date_field, '<', context['date_from'])]
            else:
                domain += [(date_field, '>=', context['date_from'])]

        if context.get('journal_ids'):
            domain += [('journal_id', 'in', context['journal_ids'])]\

        if context.get('operating_unit_ids'):
            domain += [('journal_id.branch_id', 'in', context['operating_unit_ids'])]

        state = context.get('state')
        if state and state.lower() != 'all':
            domain += [('move_id.state', '=', state)]

        if context.get('company_id'):
            domain += [('company_id', '=', context['company_id'])]

        if 'company_ids' in context:
            domain += [('company_id', 'in', context['company_ids'])]

        if context.get('reconcile_date'):
            domain += ['|', ('reconciled', '=', False), '|', ('matched_debit_ids.max_date', '>', context['reconcile_date']), ('matched_credit_ids.max_date', '>', context['reconcile_date'])]

        if context.get('account_tag_ids'):
            domain += [('account_id.tag_ids', 'in', context['account_tag_ids'].ids)]

        if context.get('account_ids'):
            domain += [('account_id', 'in', context['account_ids'].ids)]

        if context.get('analytic_tag_ids'):
            domain += [('analytic_tag_ids', 'in', context['analytic_tag_ids'].ids)]

        if context.get('analytic_account_ids'):
            domain += [('analytic_account_id', 'in', context['analytic_account_ids'].ids)]

        if context.get('analytic_account_group_ids'):
            domain += [('analytic_account_id.group_id', 'in', context['analytic_account_group_ids'].ids)]

        if context.get('partner_ids'):
            domain += [('partner_id', 'in', context['partner_ids'].ids)]

        if context.get('partner_categories'):
            domain += [('partner_id.category_id', 'in', context['partner_categories'].ids)]

        where_clause = ""
        where_clause_params = []
        tables = ''
        if domain:
            print("DOMAIN NIH", domain)
            query = self._where_calc(domain)

            # Wrap the query with 'company_id IN (...)' to avoid bypassing company access rights.
            self._apply_ir_rules(query)

            tables, where_clause, where_clause_params = query.get_sql()
        return tables, where_clause, where_clause_params