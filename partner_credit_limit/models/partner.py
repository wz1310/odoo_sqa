"""File Partner"""
from ast import literal_eval
from odoo import api, fields, models, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    """ inherited res_partner object """
    _inherit = "res.partner"

    partner_pricelist_ids = fields.One2many('partner.pricelist',
        'partner_id', string='Partner Pricelist')
    partner_pricelist_discount_ids = fields.One2many('partner.pricelist.discount',
        'partner_id', string='Partner Pricelist Discount')
    credit_limit = fields.Float(string='Credit Limit', compute='_compute_current_credit',
        track_visibility='onchange')
    current_credit = fields.Float("Current Credit", compute='_compute_current_credit')
    over_due = fields.Selection(compute='_compute_current_credit', string='Status Invoice',
        selection=[('not_overdue', 'Not Over Due'), ('overdue', 'Over Due')])
    remaining_limit = fields.Float("Remaining Limit", compute='_compute_current_credit')
    black_list = fields.Selection(compute='_compute_current_credit', string='Status BlackList',
        selection=[('not_blacklist', 'Not Black List'), ('blacklist', 'Black List')])

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('is_company'):
                if vals.get('parent_id') or self.parent_id:
                    raise UserError(_('If Contacts type is Company, Parent id should be empty.'))
        res = super(ResPartner, self).create(vals_list)
        return res

    def write(self, vals):
        if vals.get('is_company'):
            if vals.get('parent_id') or self.parent_id:
                raise UserError(_('If Contacts type is Company, Parent id should be empty.'))
        res = super(ResPartner, self).write(vals)
        return res

    @api.constrains('partner_pricelist_ids')
    def _check_same_division(self):
        data = []
        for line in self.partner_pricelist_ids:
            if line.team_id and line.team_id.id not in data :
                data.append(line.team_id.id)
            else:
                if line.team_id:
                    raise ValidationError(_('Divisi %s can only be chosen once per partner' % (line.team_id.name)))

    @api.constrains('partner_pricelist_discount_ids')
    def _check_same_category(self):
        data = []
        for line in self.partner_pricelist_discount_ids:
            if line.categ_id and line.categ_id.id not in data :
                data.append(line.categ_id.id)
            else:
                if line.categ_id:
                    raise ValidationError(_('Category %s can only be chosen once per partner' % (line.categ_id.name)))

    @api.depends('partner_pricelist_ids', 'partner_pricelist_ids.credit_limit',
                 'partner_pricelist_ids.current_credit', 'partner_pricelist_ids.over_due',
                 'partner_pricelist_ids.remaining_limit', 'partner_pricelist_ids.black_list')
    def _compute_current_credit(self):
        """ this function to calculate credits"""
        for this in self:
            partner = this if this.company_type == 'company' else this.parent_id
            credit = current_credit = remaining_limit = 0
            over_due = 'not_overdue'
            black_list = 'not_blacklist'
            for line in partner.partner_pricelist_ids:
                credit += line.credit_limit
                current_credit += line.current_credit
                remaining_limit += line.remaining_limit
                if line.over_due == 'overdue':
                    over_due = 'overdue'
                if line.black_list == 'blacklist':
                    black_list = 'blacklist'
            this.update({'credit_limit':credit,
                         'current_credit':current_credit,
                         'remaining_limit':remaining_limit,
                         'over_due':over_due,
                         'black_list':black_list})

    # TUTUP KARENA MIGRASI
    def _invoice_total(self):
        ''' Replace Function Base get information from total amount '''
        account_invoice_report = self.env['account.invoice.report']
        if not self.ids:
            self.total_invoiced = 0.0
            return True
    
        user_currency_id = self.env.user.company_id.currency_id.id
        all_partners_and_children = {}
        all_partner_ids = []
        for partner in self:
            # price_total is in the company currency
            all_partners_and_children[partner] = self.with_context(active_test=False).search([('id', 'child_of', partner.id)]).ids
            all_partner_ids += all_partners_and_children[partner]
    
        # searching account.invoice.report via the ORM is comparatively expensive
        # (generates queries "id in []" forcing to build the full table).
        # In simple cases where all invoices are in the same currency than the user's company
        # access directly these elements
    
        # generate where clause to include multicompany rules
        where_query = account_invoice_report._where_calc([
            ('partner_id', 'in', all_partner_ids), ('state', 'not in', ['draft', 'cancel']),
            ('type', 'in', ('out_invoice', 'out_refund'))
        ])
        account_invoice_report._apply_ir_rules(where_query, 'read')
        from_clause, where_clause, where_clause_params = where_query.get_sql()
    
        # price_total is in the company currency
        query = """
                    SELECT sum(amount_total)as total, partner_id FROM account_move a WHERE id in (
                        SELECT move_id
                            FROM account_invoice_report account_invoice_report
                            WHERE %s
                   ) GROUP BY partner_id
                """ % where_clause
        self.env.cr.execute(query, where_clause_params)
        price_totals = self.env.cr.dictfetchall()
        for partner, child_ids in all_partners_and_children.items():
            partner.total_invoiced = sum(price['total'] for price in price_totals if price['partner_id'] in child_ids)

    def action_view_partner_invoices_due(self):
        self.ensure_one()
        today = fields.Date.today()
        list_invoice = []
        for aml in self.unreconciled_aml_ids:  # unreconciled_aml_ids : fields ini gak ada :(
            user = self.env.user
            is_overdue = today > aml.date_maturity if aml.date_maturity else today > aml.date
            if is_overdue and aml.company_id == user.company_id and aml.invoice_id:
                if user.has_group('sales_team.group_sale_salesman_all_leads') or \
                    user.has_group('account.group_account_invoice'):
                    list_invoice.append(aml.invoice_id.id)
                elif user.has_group('sales_team.group_sale_salesman'):
                    if not aml.invoice_id.user_id or aml.invoice_id.user_id.id == user.id:
                        list_invoice.append(aml.invoice_id.id)
        action = self.env.ref('partner_credit_limit.action_invoice_due_tree').read()[0]
        action['domain'] = literal_eval(action['domain'])
        action['domain'].append(('partner_id', 'child_of', self.id))
        action['domain'].append(('id', 'in', list_invoice))
        return action
    
    def btn_add_pricelist(self):
        view_id = self.env.ref('partner_credit_limit.partner_pricelist_view_form').id
        return {
            'name':'Partner Pricelist',
            'view_type':'form',
            'view_mode':'tree',
            'views':[(view_id,'form')],
            'res_model':'partner.pricelist',
            'view_id':view_id,
            'type':'ir.actions.act_window',
            'target':'new',
            'context':{
                'default_partner_id':self.id,
                }
               }

class BlackList(models.Model):
    """ Create black_list object """
    _name = "black.list"
    _description = "Black List"

    name = fields.Char()
    min = fields.Integer('Minimum Days')
