from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero


class InherietBudgetControl(models.Model):
    _name = 'inheriet.budget.control'

    name = fields.Char()
    value = fields.Integer()
    value2 = fields.Float(compute="_value_pc", store=True)
    description = fields.Text()

class Inherit_crossovered_budget_lines(models.Model):
    _inherit = 'crossovered.budget.lines'

    remaining_amount = fields.Monetary(compute='_remain_amount',store=True)
    remainings_amount = fields.Monetary(compute='_remain_amount',string='Remaining Amount')
    status = fields.Selection(selection=[
            ('open', 'Open'),
            ('close', 'Close')],string='Status',default='open')

    @api.depends('remainings_amount')
    def _remain_amount(self):
        for x in self:
            if x._origin.id:
                practical = x.practical_amount
                plan = x.planned_amount
                x.remaining_amount = plan - practical
                x.remainings_amount = x.remaining_amount

class Inherit_crossovered_budget(models.Model):
    _inherit = 'crossovered.budget'

    def tesz(self):
        for rec in self:
            rec.tes()

    def maxs_id(self):
        sql=""" UPDATE crossovered_budget_lines SET max_id=(SELECT max(id) FROM crossovered_budget_lines) """
        cr= self.env.cr
        cr.execute(sql,())

    def close_budget(self):
        sql=""" UPDATE crossovered_budget_lines SET status='close' WHERE id < (SELECT max(id) FROM crossovered_budget_lines) 
        AND crossovered_budget_id =%s """
        cr= self.env.cr
        cr.execute(sql,(self._origin.id,))

    def update_planned_amount(self):
        sql="""UPDATE crossovered_budget_lines SET planned_amount=(SELECT remaining_amount FROM crossovered_budget_lines WHERE id < (SELECT max(id) FROM crossovered_budget_lines) 
        AND crossovered_budget_id =%s) WHERE id >= (SELECT max(id) FROM crossovered_budget_lines)
        AND crossovered_budget_id =%s
        ORDER BY id DESC LIMIT 1"""
        cr= self.env.cr
        cr.execute(sql,(self._origin.id,self._origin.id))

    def tes(self):
        result = self.env['crossovered.budget.lines'].search([('crossovered_budget_id','=',self._origin.id)],limit=1, order='id')
        for res in result:
            idku = res['id']
            crossovered_budget_id = res['crossovered_budget_id']
            analytic_account_id = res['analytic_account_id']
            general_budget_id = res['general_budget_id']
            date_from = res['date_from'] + relativedelta(months=1)
            date_from_line = res['date_from']
            date_to = res['date_to'] + relativedelta(months=1)
            date_to_line = res['date_to']
            paid_date = res['paid_date']
            planned_amount = res['planned_amount']
            company_id = res['company_id']
            crossovered_budget_state = res['crossovered_budget_state']
            create_uid = res['create_uid']
            create_date = res['create_date']
            write_uid = res['write_uid']
            write_date = res['write_date']
            remaining_amount = res['remaining_amount']

        if date_to_line == self.date_to:
            sqlx = self.env.cr.execute('UPDATE crossovered_budget_lines SET status=%s WHERE id <= (SELECT max(id) FROM crossovered_budget_lines)AND crossovered_budget_id =%s',
                ('close',self._origin.id,))
            return sqlx
        elif date_from_line > self.date_to:
            sqly = self.env.cr.execute('UPDATE crossovered_budget_lines SET status=%s WHERE id <= (SELECT max(id) FROM crossovered_budget_lines)AND crossovered_budget_id =%s',
                ('close',self._origin.id,))
            return sqly

        sql="""SELECT (date_trunc('MONTH', (%s)) + INTERVAL '1 MONTH - 1 day')::DATE
        FROM crossovered_budget_lines
        WHERE id <= (SELECT max(id) FROM crossovered_budget_lines)AND crossovered_budget_id =%s
        ORDER BY id DESC LIMIT 1"""
        cr= self.env.cr
        cr.execute(sql,(date_from,self._origin.id,))
        resuks= cr.fetchall()
        for res in resuks:
            cuakz = res[0]

        sheet = self.env['crossovered.budget.lines'].create({
            'id': idku,
            'crossovered_budget_id': crossovered_budget_id.id,
            'analytic_account_id': analytic_account_id.id,
            'general_budget_id': general_budget_id.id,
            'date_from': date_from,
            'date_to': cuakz,
            'paid_date': paid_date,
            'planned_amount': remaining_amount,
            'company_id': company_id.id,
            'crossovered_budget_state': crossovered_budget_state,
            'create_uid': create_uid,
            'create_date': create_date,
            'write_uid': write_uid,
            'write_date': write_date
            })
        self.close_budget()
        return sheet

