# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import copy
import ast

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.tools.misc import formatLang
from odoo.tools import float_is_zero, ustr
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

class ReportAccountFinancialReport(models.Model):
    _inherit = "account.financial.html.report"

    def _get_columns_name(self, options):
        """replace base and add condition based on name report"""

        print('>>> _get_report_name() : ' + str(self._get_report_name()))

        columns = [{'name': ''}]
        if self.debit_credit and not options.get('comparison', {}).get('periods', False):
            columns += [{'name': _('Debit'), 'class': 'number'}, {'name': _('Credit'), 'class': 'number'}]
        if not self.filter_date:
            if self.date_range:
                self.filter_date = {'mode': 'range', 'filter': 'this_year'}
            else:
                self.filter_date = {'mode': 'single', 'filter': 'today'}

        model = self.env.context.get('model')
        id_model = self.env.context.get('id')
        if model and id_model:
            financial_report_id = self.env[model].browse(id_model)
        if self._get_report_name() in ('Profit and Loss Statement', 'Balance Sheet', 'Executive Summary', 'Neraca', 'Profit and Loss') or\
                financial_report_id.name == ('Profit and Loss Statement', 'Balance Sheet', 'Executive Summary', 'Neraca', 'Profit and Loss'):

            # Updated by : MIS@SanQua
            # At: 20/12/2021
            # Author: Peter Susanto
            # Description: Profit and Loss Statement need to have default compare each month. Total month is 6 months.
            #              it needs force the filter

            if self._get_report_name() == 'Profit and Loss':
                # print('>>> Filter Date: ' + str(self.filter_date))
                # print('>>> Number of Periods : ' + str(options['comparison']['number_period']))
                # print('>>> Periods : ' + str(options['comparison'].get('periods')))
                options['comparison']['number_period'] = 5
                self.filter_date = {'mode': 'range', 'filter': 'this_year'}

            if options.get('comparison') and options['comparison'].get('periods'):
                for period in sorted(options['comparison']['periods'], key = lambda i: i['date_from']):
                    columns += [{'name': period.get('string'), 'class': 'number'}]
                columns += [{'name': self.format_date(options), 'class': 'number'}]
                if options['comparison'].get('number_period') == 1 and not options.get('groups'):
                    columns += [{'name': '%', 'class': 'number'}]
            else:
                columns += [{'name': self.format_date(options), 'class': 'number'}]
        else:

            columns += [{'name': self.format_date(options), 'class': 'number'}]
            if options.get('comparison') and options['comparison'].get('periods'):
                for period in options['comparison']['periods']:
                    columns += [{'name': period.get('string'), 'class': 'number'}]
                if options['comparison'].get('number_period') == 1 and not options.get('groups'):
                    columns += [{'name': '%', 'class': 'number'}]

        if options.get('groups', {}).get('ids'):
            columns_for_groups = []
            for column in columns[1:]:
                for ids in options['groups'].get('ids'):
                    group_column_name = ''
                    for index, id in enumerate(ids):
                        column_name = self._get_column_name(id, options['groups']['fields'][index])
                        group_column_name += ' ' + column_name
                    columns_for_groups.append({'name': column.get('name') + group_column_name, 'class': 'number'})
            columns = columns[:1] + columns_for_groups
        return columns

    def _get_lines(self, options, line_id=None):
        """replace function base and add context report name"""
        line_obj = self.line_ids
        if line_id:
            line_obj = self.env['account.financial.html.report.line'].search([('id', '=', line_id)])
        if options.get('comparison') and options.get('comparison').get('periods'):
            line_obj = line_obj.with_context(periods=options['comparison']['periods'])
        if options.get('ir_filters'):
            line_obj = line_obj.with_context(periods=options.get('ir_filters'))

        currency_table = self._get_currency_table()
        domain, group_by = self._get_filter_info(options)

        if group_by:
            options['groups'] = {}
            options['groups']['fields'] = group_by
            options['groups']['ids'] = self._get_groups(domain, group_by)

        amount_of_periods = len((options.get('comparison') or {}).get('periods') or []) + 1
        amount_of_group_ids = len(options.get('groups', {}).get('ids') or []) or 1
        linesDicts = [[{} for _ in range(0, amount_of_group_ids)] for _ in range(0, amount_of_periods)]
        #add context report name
        res = line_obj.with_context(
            filter_domain=domain, report_name=self._get_report_name()
        )._get_lines(self, currency_table, options, linesDicts)
        return res

class AccountFinancialReportLine(models.Model):
    _inherit = "account.financial.html.report.line"

    def _get_lines(self, financial_report, currency_table, options, linesDicts):
        """replace base and sorted comparison"""
        report = ''
        final_result_table = []
        comparison_table = [options.get('date')]
        comparison_table += options.get('comparison') and options['comparison'].get('periods', []) or []
        model = self.env.context.get('model')
        id_model = self.env.context.get('id')
        report_name = self.env.context.get('report_name')
        if model and id_model:
            financial_report_id = self.env[model].browse(id_model)
            if financial_report_id.name in ('Profit and Loss Statement', 'Balance Sheet', 'Executive Summary', 'Neraca'):
                comparison_table = sorted(comparison_table, key = lambda i: i['date_from'])
                report = financial_report_id.name
        if report_name and report_name in ('Profit and Loss Statement', 'Balance Sheet', 'Executive Summary', 'Neraca'):
            comparison_table = sorted(comparison_table, key = lambda i: i['date_from'])
            report = report_name
        currency_precision = self.env.company.currency_id.rounding
        # build comparison table
        for line in self:
            res = []
            debit_credit = len(comparison_table) == 1
            domain_ids = {'line'}
            k = 0
            for period in comparison_table:
                date_from = period.get('date_from', False)
                date_to = period.get('date_to', False) or period.get('date', False)
                date_from, date_to, strict_range = line.with_context(date_from=date_from, date_to=date_to)._compute_date_range()

                r = line.with_context(date_from=date_from,
                                      date_to=date_to,
                                      strict_range=strict_range)._eval_formula(financial_report,
                                                                               debit_credit,
                                                                               currency_table,
                                                                               linesDicts[k],
                                                                               groups=options.get('groups'))
                debit_credit = False
                res.extend(r)
                for column in r:
                    domain_ids.update(column)
                k += 1

            res = line._put_columns_together(res, domain_ids)

            if line.hide_if_zero and all([float_is_zero(k, precision_rounding=currency_precision) for k in res['line']]):
                continue

            # Post-processing ; creating line dictionnary, building comparison, computing total for extended, formatting
            vals = {
                'id': line.id,
                'name': line.name,
                'level': line.level,
                'class': 'o_account_reports_totals_below_sections' if self.env.company.totals_below_sections else '',
                'columns': [{'name': l} for l in res['line']],
                'unfoldable': len(domain_ids) > 1 and line.show_domain != 'always',
                'unfolded': line.id in options.get('unfolded_lines', []) or line.show_domain == 'always',
                'page_break': line.print_on_new_page,
            }
            if financial_report.tax_report and line.domain and not line.action_id:
                vals['caret_options'] = 'tax.report.line'

            if line.action_id:
                vals['action_id'] = line.action_id.id
            domain_ids.remove('line')
            lines = [vals]
            groupby = line.groupby or 'aml'
            if line.id in options.get('unfolded_lines', []) or line.show_domain == 'always':
                if line.groupby:
                    domain_ids = sorted(list(domain_ids), key=lambda k: line._get_gb_name(k))
                for domain_id in domain_ids:
                    name = line._get_gb_name(domain_id)
                    if not self.env.context.get('print_mode') or not self.env.context.get('no_format'):
                        name = name[:40] + '...' if name and len(name) >= 45 else name
                    vals = {
                        'id': domain_id,
                        'name': name,
                        'level': line.level,
                        'parent_id': line.id,
                        'columns': [{'name': l} for l in res[domain_id]],
                        'caret_options': groupby == 'account_id' and 'account.account' or groupby,
                        'financial_group_line_id': line.id,
                    }
                    if line.financial_report_id.name == 'Aged Receivable':
                        vals['trust'] = self.env['res.partner'].browse([domain_id]).trust
                    lines.append(vals)
                if domain_ids and self.env.company.totals_below_sections:
                    lines.append({
                        'id': 'total_' + str(line.id),
                        'name': _('Total') + ' ' + line.name,
                        'level': line.level,
                        'class': 'o_account_reports_domain_total',
                        'parent_id': line.id,
                        'columns': copy.deepcopy(lines[0]['columns']),
                    })
            

            for vals in lines:
                if len(comparison_table) == 2 and not options.get('groups'):
                    vals['columns'].append(line.with_context(report_name=report)._build_cmp(vals['columns'][0]['name'], vals['columns'][1]['name']))
                    for i in [0, 1]:
                        vals['columns'][i] = line._format(vals['columns'][i])
                else:
                    vals['columns'] = [line._format(v) for v in vals['columns']]
                if not line.formulas:
                    vals['columns'] = [{'name': ''} for k in vals['columns']]
            if len(lines) == 1:
                new_lines = line.children_ids._get_lines(financial_report, currency_table, options, linesDicts)
                if new_lines and line.formulas:
                    if self.env.company.totals_below_sections:
                        divided_lines = self._divide_line(lines[0])
                        result = [divided_lines[0]] + new_lines + [divided_lines[-1]]
                    else:
                        result = [lines[0]] + new_lines
                else:
                    if not new_lines and not lines[0]['unfoldable'] and line.hide_if_empty:
                        lines = []
                    result = lines + new_lines
            else:
                result = lines
            final_result_table += result
        return final_result_table

    def _build_cmp(self, balance, comp):
        """replace function based and add condition based on report name"""
        if comp != 0:
            multiplier = 1
            report = self.env.context.get('report_name')
            if report and report in ('Profit and Loss Statement', 'Balance Sheet', 'Executive Summary', 'Neraca'):
                multiplier = -1
            res = round((balance - comp) / comp * 100 * multiplier, 1)
            # Avoid displaying '-0.0%'.
            if float_is_zero(res, precision_rounding=0.1):
                res = 0.0
            # In case the comparison is made on a negative figure, the color should be the other
            # way around. For example:
            #                       2018         2017           %
            # Product Sales      1000.00     -1000.00     -200.0%
            #
            # The percentage is negative, which is mathematically correct, but my sales increased
            # => it should be green, not red!
            if (res > 0) != (self.green_on_positive and comp > 0):
                return {'name': str(res) + '%', 'class': 'number color-red'}
            else:
                return {'name': str(res) + '%', 'class': 'number color-green'}
        else:
            return {'name': _('n/a')}
