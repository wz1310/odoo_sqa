# -*- coding: utf-8 -*-
from datetime import timedelta
from datetime import datetime
from odoo import models, fields, api


class MisSumBudget(models.Model):
    _name = 'mis.summary.budget'
    _description = 'mis_summary_budget'

    budget_pos = fields.Many2one('account.budget.post',string="Budgetary Position",domain="[('company_id', '=', company_id)]")
    acc_group = fields.Many2one('account.analytic.group',string="Analytic Group",domain="[('company_id', '=', company_id)]")
    date_paid = fields.Date(string="Paid Date")
    plan_amt = fields.Float(string="Planned Amount")
    prac_amt = fields.Float(string="Practical Amount", compute='prac_amount')
    acv_amt = fields.Float(string="Achievement",compute='_compute_percent')
    budget_cros_id = fields.Many2one('crossovered.budget')
    state = fields.Selection(related='budget_cros_id.state', store=True)
    theoritical_amount = fields.Float(compute='_compute_theoritical_amount', string='Theoretical Amount')
    date_start = fields.Date(related='budget_cros_id.date_from', store=True,string="Month")
    date_end = fields.Date(related='budget_cros_id.date_to', store=True, string="Year")
    company_id = fields.Many2one('res.company',default=lambda self: self.env.company.id,string="Company")

    def prac_amount(self):
        for line in self:
            acc_ids = line.budget_pos.account_ids.ids
            date_to = line.budget_cros_id.date_to
            date_from = line.budget_cros_id.date_from
            if line.acc_group.id:
                analytic_line_obj = self.env['account.analytic.line']
                anl_acc = self.env['account.analytic.account'].search([('group_id','=',line.acc_group.id)]).mapped('id')
                domain = [('account_id', 'in', anl_acc),
                          ('date', '>=', line.budget_cros_id.date_from),
                          ('date', '<=', line.budget_cros_id.date_to),
                          ]
                if acc_ids:
                    domain += [('general_account_id', 'in', acc_ids)]

                where_query = analytic_line_obj._where_calc(domain)
                analytic_line_obj._apply_ir_rules(where_query, 'read')
                from_clause, where_clause, where_clause_params = where_query.get_sql()
                select = "SELECT SUM(amount) from " + from_clause + " where " + where_clause

            else:
                aml_obj = self.env['account.move.line']
                domain = [('account_id', 'in',
                           line.budget_pos.account_ids.ids),
                          ('date', '>=', line.budget_cros_id.date_from),
                          ('date', '<=', line.budget_cros_id.date_to),
                          ('move_id.state', '=', 'posted')
                          ]
                where_query = aml_obj._where_calc(domain)
                aml_obj._apply_ir_rules(where_query, 'read')
                from_clause, where_clause, where_clause_params = where_query.get_sql()
                select = "SELECT sum(credit)-sum(debit) from " + from_clause + " where " + where_clause

            self.env.cr.execute(select, where_clause_params)
            line.prac_amt = self.env.cr.fetchone()[0] or 0.0

    def action_open_budget(self):
        if self.acc_group:
            # if there is an analytic account, then the analytic items are loaded
            anl_acc = self.env['account.analytic.account'].search([('group_id','=',self.acc_group.id)]).mapped('id')
            action = self.env['ir.actions.act_window'].for_xml_id('analytic', 'account_analytic_line_action_entries')
            action['domain'] = [('account_id', 'in', anl_acc),
                                ('date', '>=', self.budget_cros_id.date_from),
                                ('date', '<=', self.budget_cros_id.date_to)
                                ]
            if self.budget_pos:
                action['domain'] += [('general_account_id', 'in', self.budget_pos.account_ids.ids)]
        else:
            # otherwise the journal entries booked on the accounts of the budgetary postition are opened
            action = self.env['ir.actions.act_window'].for_xml_id('account', 'action_account_moves_all_a')
            action['domain'] = [('account_id', 'in',
                                 self.budget_pos.account_ids.ids),
                                ('date', '>=', self.budget_cros_id.date_from),
                                ('date', '<=', self.budget_cros_id.date_to)
                                ]
        return action

    def _compute_percent(self):
        for line in self:
            if line.theoritical_amount != 0.00:
                line.acv_amt = float((line.prac_amt or 0.0) / line.theoritical_amount)
            else:
                line.acv_amt = 0.00

    def _compute_theoritical_amount(self):
        # beware: 'today' variable is mocked in the python tests and thus, its implementation matter
        today = fields.Date.today()
        for line in self:
            if line.date_paid:
                if today <= line.date_paid:
                    theo_amt = 0.00
                else:
                    theo_amt = line.plan_amt
            else:
                # One day is added since we need to include the start and end date in the computation.
                # For example, between April 1st and April 30th, the timedelta must be 30 days.
                if line.budget_cros_id:
                    line_timedelta = line.budget_cros_id.date_to - line.budget_cros_id.date_from + timedelta(days=1)
                    elapsed_timedelta = today - line.budget_cros_id.date_from + timedelta(days=1)
                    if elapsed_timedelta.days < 0:
                        # If the budget line has not started yet, theoretical amount should be zero
                        theo_amt = 0.00
                    elif line_timedelta.days > 0 and today < line.budget_cros_id.date_to:
                        # If today is between the budget line date_from and date_to
                        theo_amt = (elapsed_timedelta.total_seconds() / line_timedelta.total_seconds()) * line.plan_amt
                    else:
                        theo_amt = line.plan_amt
            line.theoritical_amount = theo_amt

class MisInhersumBudget(models.Model):
    _inherit = 'crossovered.budget'

    mis_sum_budget = fields.One2many('mis.summary.budget','budget_cros_id')

    @api.constrains('mis_sum_budget')
    def change_mis_sum_budget(self):
    	self.crossovered_budget_line = [(5,0)]
    	anl_acc =  self.env['account.analytic.account']
    	for x in self.mis_sum_budget:
    		for y in anl_acc.search([('group_id','=',x.acc_group.id),('group_id','!=',False)]):
    			data = {
    			'general_budget_id':x.budget_pos.id,
    			'analytic_account_id':y.id,
    			'planned_amount':0
    			}
    			self.crossovered_budget_line = [(0,0,data)]


class MisSku(models.Model):
    _name = 'mis.sku'
    _description = 'mis_sku'

    name = fields.Char(string="SKU")
    group = fields.Many2one('mis.grouping.sku',string="Group")
    date = fields.Date(default=datetime.today(),string="Date")


class MisGorupSku(models.Model):
    _name = 'mis.grouping.sku'
    _description = 'mis_grouping_sku'

    name = fields.Char(string="Group for SKU")
    date = fields.Date(default=datetime.today(),string="Date")


class MisDivBudget(models.Model):
    _inherit = 'account.budget.post'

    divider = fields.Many2one('mis.grouping.sku',string="Divider")
    bp_group = fields.Many2one('mis.grouping.bp',string="Group")


class MisGroupBP(models.Model):
    _name = 'mis.grouping.bp'

    name = fields.Char(string="Name")
    company_id = fields.Many2one('res.company',default=lambda self: self.env.company.id,string="Company")


class MisAnlGroup(models.Model):
    _inherit = 'account.analytic.group'

    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', ondelete='cascade',check_company=True)