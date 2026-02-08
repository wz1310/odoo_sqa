# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError,RedirectWarning,AccessError

class MisRestPartner(models.Model):
    _inherit = 'res.partner'
    is_driver = fields.Boolean()
    sanqua_nik = fields.Char(string='NIK Sanqua')

    # partner_pricelist_ids = fields.One2many('partner.pricelist',
    #     'partner_id', string='Partner Pricelist')

    def validate_vat(self,vals):
        for rec in self:
            # if vals and len(vals)!=15:
            # update vat into 16 digit by andri 22 juli 2022
            if vals and len(vals)<15:
                raise UserError(_("%s for %s must be 16 digit!") % (rec._fields.get('vat'). string,rec.name))

    def write(self, vals):
        if vals.get('is_company'):
            if vals.get('parent_id') or self.parent_id:
                raise UserError(_('If Contacts type is Company, Parent id should be empty.'))

        res = super(MisRestPartner, self).write(vals)
        for partner in self:
            partner.child_ids.write({'company_id': False})
        return res

    @api.constrains('code')
    def _check_code(self):
        if self.code:
            qwr = """SELECT code FROM res_partner WHERE code = %s AND "state" NOT IN ('draft', 'reject')"""
            self.env.cr.execute(qwr,(self.code,))
            result = self.env.cr.dictfetchall()
            if len(result)>0:
                raise UserError(_("Code already exist ..."))


class MisCustomPartnerPricelist(models.Model):
    _name = 'custom.partner.pricelist'

    partner_id = fields.Many2one('res.partner', 'Partner',
        ondelete='cascade', index=True, required=True)
    team_id = fields.Many2one('crm.team', 'Divisi', index=True, required=True)
    team_member_ids = fields.Many2many('res.users',compute="_compute_team_member_ids")
    user_id = fields.Many2one('res.users', string='Salesperson')
    pricelist_id = fields.Many2one('product.pricelist',string='Pricelist')
    customer_group = fields.Many2one('customer.group', string='Customer Group')
    payment_term_id = fields.Many2one('account.payment.term', string='Term of Payments')
    credit_limit = fields.Float('Credit Limit', default=0.0)
    current_credit = fields.Float("Current Credit")
    over_due = fields.Selection(string='Over Due',
        selection=[('not_overdue', 'Not Over Due'), ('overdue', 'Over Due')])
    remaining_limit = fields.Float("Remaining Limit")
    black_list = fields.Selection(string='Status BlackList',
        selection=[('not_blacklist', 'Not Black List'), ('blacklist', 'Black List')],
        default='not_blacklist')
    sales_admin_id = fields.Many2one('res.users', string='Sales admin')


    @api.depends('team_id')
    def _compute_team_member_ids(self):
        for rec in self:
            rec.team_member_ids = rec.team_id.sales_user_ids.ids