# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import copy
import ast
import io
import datetime

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.tools.misc import formatLang
from odoo.tools import float_is_zero, ustr
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools.misc import xlsxwriter

class ReportAccountFinancialReporta(models.Model):
	_inherit = "account.financial.html.report"

	def _get_templates(self):
		templates = super(ReportAccountFinancialReporta, self)._get_templates()
		if self._get_report_name() == 'Profit and Loss Statement':
			templates['main_template'] = 'mis_financial_report_company_title.profit_loss'
		elif self._get_report_name() == 'Profit and Loss':
			templates['main_template'] = 'mis_financial_report_company_title.profit_loss'
		return templates

class ReportAccountFinancialReportb(models.AbstractModel):
	_inherit = "account.partner.ledger"

	def _get_templates(self):
		templates = super(ReportAccountFinancialReportb, self)._get_templates()
		if self._get_report_name() == 'Partner Ledger':
			templates['main_template'] = 'mis_financial_report_company_title.part_ledger'
		return templates

	@api.model
	def _get_query_amls(self, options, expanded_partner=None, offset=None, limit=None):
		unfold_all = options.get('unfold_all') or (self._context.get('print_mode') and not options['unfolded_lines'])
		if expanded_partner:
			domain = [('partner_id', '=', expanded_partner.id)]
		elif unfold_all:
			domain = []
		elif options['unfolded_lines']:
			domain = [('partner_id', 'in', [int(line[8:]) for line in options['unfolded_lines']])]
		new_options = self._get_options_sum_balance(options)
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
			WHERE %s
			ORDER BY account_move_line.date ASC
			''' % (ct_query, where_clause)
		if offset:
			query += ' OFFSET %s '
			where_params.append(offset)
		if limit:
			query += ' LIMIT %s '
			where_params.append(limit)
		return query, where_params

class ReportAccountFinancialReportc(models.AbstractModel):
	_inherit = "account.aged.receivable"

	def _get_templates(self):
		templates = super(ReportAccountFinancialReportc, self)._get_templates()
		if self._get_report_name() == 'Aged Receivable':
			templates['main_template'] = 'mis_financial_report_company_title.age_receive'
		return templates

class ReportAccountFinancialReportd(models.AbstractModel):
	_inherit = "account.aged.payable"

	def _get_templates(self):
		templates = super(ReportAccountFinancialReportd, self)._get_templates()
		if self._get_report_name() == 'Aged Payable':
			templates['main_template'] = 'mis_financial_report_company_title.age_pay'
		return templates

class ReportAccountFinancialReporte(models.AbstractModel):
	_inherit = "account.coa.report"

	def _get_templates(self):
		templates = super(ReportAccountFinancialReporte, self)._get_templates()
		if self._get_report_name() == 'Trial Balance':
			templates['main_template'] = 'mis_financial_report_company_title.tri_balance'
		return templates

class ReportAccountFinancialReportf(models.AbstractModel):
	_inherit = "account.consolidated.journal"

	def _get_templates(self):
		templates = super(ReportAccountFinancialReportf, self)._get_templates()
		if self._get_report_name() == 'Consolidated Journals':
			templates['main_template'] = 'mis_financial_report_company_title.cons_jurnal'
		return templates

class ReportAccountFinancialReportg(models.AbstractModel):
	_inherit = "account.generic.tax.report"

	def _get_templates(self):
		templates = super(ReportAccountFinancialReportg, self)._get_templates()
		if self._get_report_name() == 'Tax Report':
			templates['main_template'] = 'mis_financial_report_company_title.tax_report'
		return templates

class ReportAccountFinancialReporth(models.AbstractModel):
	_inherit = "account.general.ledger"

	def _get_templates(self):
		templates = super(ReportAccountFinancialReporth, self)._get_templates()
		if self._get_report_name() == 'General Ledger':
			templates['main_template'] = 'mis_financial_report_company_title.gen_bal'
		return templates

class ReportAccountFinancialReports(models.AbstractModel):
	_inherit = "account.report"

	def get_xlsx(self, options, response=None):
		output = io.BytesIO()
		workbook = xlsxwriter.Workbook(output, {'in_memory': True})
		sheet = workbook.add_worksheet(self._get_report_name()[:31])

		date_default_col1_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2, 'num_format': 'yyyy-mm-dd'})
		date_default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'num_format': 'yyyy-mm-dd'})
		default_col1_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2})
		default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})
		title_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2})
		no_title_style = workbook.add_format({'font_name': 'Arial', 'bold': True})
		com_title_style = workbook.add_format({'font_name': 'Arial', 'bold': True,'font_size': 14})
		rep_title_style = workbook.add_format({'font_name': 'Arial', 'bold': True,'font_size': 13})
		super_col_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'align': 'center'})
		level_0_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 13, 'bottom': 6, 'font_color': '#666666'})
		level_1_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 13, 'bottom': 1, 'font_color': '#666666'})
		level_2_col1_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666', 'indent': 1})
		level_2_col1_total_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666'})
		level_2_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666'})
		level_3_col1_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2})
		level_3_col1_total_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666', 'indent': 1})
		level_3_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})

		#Set the first column width to 50
		sheet.set_column(2, 0, 50)
		sheet.set_column(0, 1, 50)

		super_columns = self._get_super_columns(options)
		y_offset = bool(super_columns.get('columns')) and 1 or 0

		sheet.write(y_offset, 0, '', title_style)

		# Todo in master: Try to put this logic elsewhere
		x = super_columns.get('x_offset', 0)
		for super_col in super_columns.get('columns', []):
			cell_content = super_col.get('string', '').replace('<br/>', ' ').replace('&nbsp;', ' ')
			x_merge = super_columns.get('merge')
			if x_merge and x_merge > 1 and self._get_report_name() != 'Trial Balance':
				sheet.merge_range(0, x, 0, x + (x_merge - 1), cell_content, super_col_style)
				x += x_merge
			elif x_merge and x_merge > 1 and self._get_report_name() == 'Trial Balance':
				sheet.merge_range(2, x, 2, x + (x_merge - 1), cell_content, super_col_style)
				x += x_merge
			else:
				sheet.write(0, x, cell_content, super_col_style)
				x += 1
		for row in self.get_header(options):
			x = 0
			for column in row:
				colspan = column.get('colspan', 1)
				header_label = column.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' ')
				reports_prof = "Laporan Profit and Loss"
				reports_balan = "Laporan Balance Sheet"
				reports_exe = "Laporan Executive Summary"
				reports_partner = "Laporan Partner Ledger"
				reports_aged = "Laporan Aged Receivable"
				reports_pay = "Laporan Aged Payable"
				reports_gen = "Laporan General Ledger"
				reports_trial = "Laporan Trial Balance"
				reports_cons = "Laporan Consolidated Journals"
				reports_tax = "Laporan Tax Report"
				companies = self.env['res.company'].search([('id','=',self.env.company.ids)])
				titles = ["Profit and Loss","Profit and Loss Statement","Balance Sheet","Executive Summary","Partner Ledger"
				,"Aged Receivable","Aged Payable","Trial Balance","General Ledger","Consolidated Journals","Tax Report"]
				rep_names = self._get_report_name() not in titles
				if colspan == 1 and rep_names :
					sheet.write(y_offset, x, header_label, title_style)
				elif colspan == 1 and self._get_report_name() == 'Profit and Loss':
					sheet.write(y_offset, colspan-1, companies.name, com_title_style)
					sheet.write(y_offset+1, colspan-1, reports_prof, rep_title_style)
					sheet.write(y_offset+1, x, header_label, rep_title_style)
				elif colspan == 1 and self._get_report_name() == 'Profit and Loss Statement':
					sheet.write(y_offset, colspan-1, companies.name, com_title_style)
					sheet.write(y_offset+1, colspan-1, reports_prof, rep_title_style)
					sheet.write(y_offset+1, x, header_label, rep_title_style)
				elif colspan == 1 and self._get_report_name() == 'Balance Sheet':
					sheet.write(y_offset, colspan-1, companies.name, com_title_style)
					sheet.write(y_offset+1, colspan-1, reports_balan, rep_title_style)
					sheet.write(y_offset+1, x, header_label, rep_title_style)
				elif colspan == 1 and self._get_report_name() == 'Executive Summary':
					sheet.write(y_offset, colspan-1, companies.name, com_title_style)
					sheet.write(y_offset+1, colspan-1, reports_exe, rep_title_style)
					sheet.write(y_offset+1, x, header_label, rep_title_style)
				elif colspan == 1 and self._get_report_name() == 'Partner Ledger':
					sheet.write(y_offset, colspan-1, companies.name, com_title_style)
					sheet.write(y_offset+1, colspan-1, reports_partner, rep_title_style)
					sheet.write(y_offset+2, x, header_label, rep_title_style)
				elif colspan == 1 and self._get_report_name() == 'Aged Receivable':
					sheet.write(y_offset, colspan-1, companies.name, com_title_style)
					sheet.write(y_offset+1, colspan-1, reports_aged, rep_title_style)
					sheet.write(y_offset+2, x, header_label, rep_title_style)
				elif colspan == 1 and self._get_report_name() == 'Aged Payable':
					sheet.write(y_offset, colspan-1, companies.name, com_title_style)
					sheet.write(y_offset+1, colspan-1, reports_pay, rep_title_style)
					sheet.write(y_offset+2, x, header_label, rep_title_style)
				elif colspan == 1 and self._get_report_name() == 'General Ledger':
					sheet.write(0, colspan-1, companies.name, com_title_style)
					sheet.write(1, colspan-1, reports_gen, rep_title_style)
					sheet.write(y_offset+2, x, header_label, rep_title_style)
				elif colspan == 1 and self._get_report_name() == 'Trial Balance':
					sheet.write(0, colspan-1, companies.name, com_title_style)
					sheet.write(1, colspan-1, reports_trial, rep_title_style)
					sheet.write(y_offset+2, x, header_label, rep_title_style)
				elif colspan == 1 and self._get_report_name() == 'Consolidated Journals':
					sheet.write(y_offset, colspan-1, companies.name, com_title_style)
					sheet.write(y_offset+1, colspan-1, reports_cons, rep_title_style)
					sheet.write(y_offset+2, x, header_label, rep_title_style)
				elif colspan == 1 and self._get_report_name() == 'Tax Report':
					sheet.write(y_offset, colspan-1, companies.name, com_title_style)
					sheet.write(y_offset+1, colspan-1, reports_tax, rep_title_style)
					sheet.write(y_offset+2, x, header_label, rep_title_style)
				else:
					sheet.merge_range(y_offset, x, y_offset, x + colspan - 1, header_label, title_style)
				x += colspan
			y_offset += 3
		ctx = self._set_context(options)
		ctx.update({'no_format':True, 'print_mode':True, 'prefetch_fields': False})
		# deactivating the prefetching saves ~35% on get_lines running time
		lines = self.with_context(ctx)._get_lines(options)

		if options.get('hierarchy'):
			lines = self._create_hierarchy(lines, options)
		if options.get('selected_column'):
			lines = self._sort_lines(lines, options)

		#write all data rows
		for y in range(0, len(lines)):
			level = lines[y].get('level')
			if lines[y].get('caret_options'):
				style = level_3_style
				col1_style = level_3_col1_style
			elif level == 0:
				y_offset += 1
				style = level_0_style
				col1_style = style
			elif level == 1:
				style = level_1_style
				col1_style = style
			elif level == 2:
				style = level_2_style
				col1_style = 'total' in lines[y].get('class', '').split(' ') and level_2_col1_total_style or level_2_col1_style
			elif level == 3:
				style = level_3_style
				col1_style = 'total' in lines[y].get('class', '').split(' ') and level_3_col1_total_style or level_3_col1_style
			else:
				style = default_style
				col1_style = default_col1_style

			#write the first column, with a specific style to manage the indentation
			cell_type, cell_value = self._get_cell_type_value(lines[y])
			if cell_type == 'date':
				sheet.write(y + y_offset, 0, cell_value, date_default_col1_style)
			else:
				sheet.write(y + y_offset, 0, cell_value, col1_style)

			#write all the remaining cells
			for x in range(1, len(lines[y]['columns']) + 1):
				cell_type, cell_value = self._get_cell_type_value(lines[y]['columns'][x - 1])
				if cell_type == 'date':
					sheet.write(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value, date_default_style)
				else:
					sheet.write(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value, style)

		workbook.close()
		output.seek(0)
		generated_file = output.read()
		output.close()

		return generated_file
		return super(ReportAccountFinancialReports, self)._get_templates(options,response)

	def _get_cell_type_value(self, cell):
		if 'date' not in cell.get('class', '') or not cell.get('name'):
			return ('text', cell.get('name', ''))
		if isinstance(cell['name'], (float, datetime.date, datetime.datetime)):
			return ('date', cell['name'])
		try:
			return ('date', cell['name'])
		except:
			return ('text', cell['name'])