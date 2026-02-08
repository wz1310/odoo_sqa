from odoo import models, api, _, fields


class report_account_consolidated_journals(models.AbstractModel):
    _name = "mis.report.summary.penjualan.bersih"
    _description = "Summary Report"
    _inherit = 'account.report'

    filter_date = {'mode': 'range', 'filter': 'this_year'}

    # Override: disable multicompany
    def _get_filter_journals(self):
        return self.env['account.journal'].search([('company_id', 'in', [self.env.company.id, False])], order="company_id, name")

    @api.model
    def _get_options(self, previous_options=None):
        options = super(report_account_consolidated_journals, self)._get_options(previous_options=previous_options)
        # We do not want multi company for this report
        options.setdefault('date', {})
        options['date'].setdefault('date_to', fields.Date.context_today(self))
        return options

    def _get_report_name(self):
        return _("Summary Report")

    def _get_columns_name(self, options):
        columns = [{'name': _('Journal Names')}, {'name': _('Debit'), 'class': 'number'}, {'name': _('Credit'), 'class': 'number'}, {'name': _('Balance'), 'class': 'number'}]
        print("OPTION", options)
        return columns