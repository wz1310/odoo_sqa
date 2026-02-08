from odoo import models, api, _, fields


class report_account_consolidated_journal(models.AbstractModel):
    _name = "test.sale"
    _description = "Test Sale"
    _inherit = 'account.report'

    filter_multi_company = None
    filter_date = {'mode': 'range', 'filter': 'this_year'}
    filter_all_entries = False
    filter_journals = True
    filter_unfold_all = False

    # Override: disable multicompany
    def _get_filter_journals(self):
        return self.env['account.journal'].search([('company_id', 'in', [self.env.company.id, False])], order="company_id, name")

    @api.model
    def _get_options(self, previous_options=None):
        options = super(report_account_consolidated_journal, self)._get_options(previous_options=previous_options)
        # We do not want multi company for this report
        options.setdefault('date', {})
        options['date'].setdefault('date_to', fields.Date.context_today(self))
        return options

    def _get_report_name(self):
        return _("Consolidated Journals")

    def _get_columns_name(self, options):
        columns = [{'name': _('Journal Name (Code)')}, {'name': _('Debit'), 'class': 'number'}, {'name': _('Credit'), 'class': 'number'}, {'name': _('Balance'), 'class': 'number'}]
        return columns

    def _get_sum(self, results, lambda_filter):
        sum_debit = self.format_value(sum([r['debit'] for r in results if lambda_filter(r)]))
        sum_credit = self.format_value(sum([r['credit'] for r in results if lambda_filter(r)]))
        sum_balance = self.format_value(sum([r['balance'] for r in results if lambda_filter(r)]))
        return [sum_debit, sum_credit, sum_balance]

    def _get_journal_line(self, options, current_journal, results, record):
        return {
                'id': 'journal_%s' % current_journal,
                'name': '%s (%s)' % (record['journal_name'], record['journal_code']),
                'level': 2,
                'columns': [{'name': n} for n in self._get_sum(results, lambda x: x['journal_id'] == current_journal)],
                'unfoldable': True,
                'unfolded': self._need_to_unfold('journal_%s' % (current_journal,), options),
            }

    def _get_account_line(self, options, current_journal, current_account, results, record):
        return {
                'id': 'account_%s_%s' % (current_account,current_journal),
                'name': '%s %s' % (record['account_code'], record['account_name']),
                'level': 3,
                'columns': [{'name': n} for n in self._get_sum(results, lambda x: x['account_id'] == current_account)],
                'unfoldable': True,
                'unfolded': self._need_to_unfold('account_%s_%s' % (current_account, current_journal), options),
                'parent_id': 'journal_%s' % (current_journal),
            }

    def _get_line_total_per_month(self, options, current_company, results):
        convert_date = self.env['ir.qweb.field.date'].value_to_html
        lines = []
        lines.append({
                    'id': 'Total_all_%s' % (current_company),
                    'name': _('Total'),
                    'class': 'total',
                    'level': 1,
                    'columns': [{'name': n} for n in self._get_sum(results, lambda x: x['company_id'] == current_company)]
        })
        lines.append({
                    'id': 'blank_line_after_total_%s' % (current_company),
                    'name': '',
                    'columns': [{'name': ''} for n in ['debit', 'credit', 'balance']]
        })
        # get range of date for company_id
        dates = []
        for record in results:
            date = '%s-%s' % (record['yyyy'], record['month'])
            if date not in dates:
                dates.append(date)
        if dates:
            lines.append({'id': 'Detail_%s' % (current_company),
                        'name': _('Details per month'),
                        'level': 1,
                        'columns': [{},{},{}]
                        })
            for date in sorted(dates):
                year, month = date.split('-')
                sum_debit = self.format_value(sum([r['debit'] for r in results if (r['month'] == month and r['yyyy'] == year) and r['company_id'] == current_company]))
                sum_credit = self.format_value(sum([r['credit'] for r in results if (r['month'] == month and r['yyyy'] == year) and r['company_id'] == current_company]))
                sum_balance = self.format_value(sum([r['balance'] for r in results if (r['month'] == month and r['yyyy'] == year) and r['company_id'] == current_company]))
                vals = {
                        'id': 'Total_month_%s_%s' % (date, current_company),
                        'name': convert_date('%s-01' % (date), {'format': 'MMM yyyy'}),
                        'level': 2,
                        'columns': [{'name': v} for v in [sum_debit, sum_credit, sum_balance]]
                }
                lines.append(vals)
        return lines