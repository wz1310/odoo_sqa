""" File partner pricelist"""
from odoo import api, fields, models, _, SUPERUSER_ID
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.exceptions import UserError



class PartnerPricelist(models.Model):
    """ new object partner pricelist """
    _name = "partner.pricelist"
    _description = "Partner Pricelist"

    partner_id = fields.Many2one('res.partner', 'Partner',
        ondelete='cascade', index=True, required=True)
    team_id = fields.Many2one('crm.team', 'Divisi', index=True, required=True)
    team_member_ids = fields.Many2many('res.users',compute="_compute_team_member_ids")

    user_id = fields.Many2one('res.users', string='Salesperson')
    credit_limit = fields.Float('Credit Limit', required=True, default=0.0)
    current_credit = fields.Float("Current Credit", compute='_compute_credit')
    over_due = fields.Selection(string='Over Due',
        selection=[('not_overdue', 'Not Over Due'), ('overdue', 'Over Due')],
        compute='_compute_credit')
    remaining_limit = fields.Float("Remaining Limit", compute='_compute_credit')
    black_list = fields.Selection(string='Status BlackList',
        selection=[('not_blacklist', 'Not Black List'), ('blacklist', 'Black List')],
        default='not_blacklist')
    pricelist_id = fields.Many2one('product.pricelist',
        string='Pricelist')
    delivery_id = fields.Many2one('delivery.carrier',
        string='Delivery Method')
    multi_discounts = fields.Char(
        string='Discounts', help='This field is used to allow multiple discounts, \
        How to used is: By adding multiple discount amounts \
        separated with by + / - or etc. \
        If you apply 10+5+2 it will apply first 10(%) discount \
        and then it will apply 5(%) on new amount and then it will apply 2(%)',
    )
    pricelist_discount_id = fields.Many2one('pricelist.discount')  #harusnya many to one object bar
    total_discount_percent = fields.Char("Total Disc %", compute='_compute_pricelist_discount_id')
    discount_amount = fields.Float("Disc Amount")
    total_discount_amount = fields.Float("Total Disc Amount", compute='_compute_pricelist_discount_id')
    company_id = fields.Many2one('res.company')

    @api.constrains('team_id','partner_id')
    def constrains_team_partner(self):
        for rec in self:
            duplicate = self.search([('team_id','=',rec.team_id.id), ('partner_id','=',rec.partner_id.id), ('id','!=',rec.id)])
            if len(duplicate):
                raise UserError(_("Pricelist Division %s for %s already defined!") % (rec.partner_id.display_name, rec.team_id.display_name,))
            


    @api.depends('team_id')
    def _compute_team_member_ids(self):
        for rec in self:
            rec.team_member_ids = rec.team_id.member_ids.ids

    @api.model
    @api.returns('self')
    def get_partner_pricelist(self, partner, team, user):
        ids = []
        if partner and team and user:
            query = """
                SELECT id FROM partner_pricelist WHERE partner_id = %s AND team_id = %s AND user_id = %s
            """

            self.env.cr.execute(query, (partner.id, team.id, user.id, ))

            query_res = self.env.cr.fetchall()
            ids = [x[0] for x in query_res]
        return self.browse(ids)

    @api.depends('pricelist_discount_id', 'pricelist_discount_id.compute_price', 'discount_amount', 'multi_discounts')
    def _compute_pricelist_discount_id(self):
        for rec in self:
            if rec.pricelist_discount_id:
                discount_amount = 0
                discount_percent = ''
                if rec.pricelist_discount_id.compute_price == 'fixed':
                    discount_amount = rec.pricelist_discount_id.fixed_price
                    
                elif rec.pricelist_discount_id.compute_price == 'percentage':
                    discount_percent = rec.pricelist_discount_id.percent_price
                
                elif rec.pricelist_discount_id.base_pricelist_discount_id.compute_price:
                    if rec.pricelist_discount_id.base_pricelist_discount_id.compute_price == 'fixed':
                        if rec.pricelist_discount_id.other_compute_price == 'fixed':
                            discount_amount = rec.pricelist_discount_id.base_pricelist_discount_id.fixed_price + rec.pricelist_discount_id.fixed_price
                        else:
                            discount_amount = rec.pricelist_discount_id.base_pricelist_discount_id.fixed_price
                            discount_percent = rec.pricelist_discount_id.percent_price
                    elif rec.pricelist_discount_id.base_pricelist_discount_id.compute_price == 'percentage':
                        if rec.pricelist_discount_id.other_compute_price == 'percentage':
                            discount_percent = rec.pricelist_discount_id.base_pricelist_discount_id.percent_price + '+' + rec.pricelist_discount_id.percent_price
                        else:
                            discount_amount = rec.pricelist_discount_id.fixed_price
                            discount_percent = rec.pricelist_discount_id.base_pricelist_discount_id.percent_price
                rec.total_discount_amount =  rec.discount_amount + discount_amount
                rec.total_discount_percent = discount_percent + '+' +  rec.multi_discounts if rec.multi_discounts else discount_percent
            else:
                rec.update({
                    'total_discount_amount':0.0,
                    'total_discount_percent':'',
                })

    def set_black_list(self):
        for rec in self:
            if rec.black_list == 'blacklist':
                rec.update({'black_list': 'not_blacklist'})
            else:
                rec.update({'black_list': 'blacklist'})

    def name_get(self):
        result = []
        for pp in self:
            result.append((pp.id, pp.partner_id.name + '/' + pp.team_id.name))
        return result

    def _generate_black_list(self):
        """ 
            this function to set black list
        """
        today_dt = datetime.now().date()
        blacklist_obj = self.env['black.list'].search([], limit =1 )
        min_blacklist = blacklist_obj.min if blacklist_obj.min else 0
        date_black_list = datetime.strftime(today_dt-relativedelta(days=min_blacklist), DF)
        date = datetime.strptime(date_black_list, DF)
        pp_ids = self.search([('black_list', '=', 'not_blacklist')])
        for pp_id in pp_ids:
            if pp_id.partner_id.company_type == 'company':
                partner = pp_id.partner_id.id 
            else: 
                partner = pp_id.partner_id.parent_id.id
            moveline_obj = self.env['account.move.line'].sudo()
            movelines = moveline_obj.search(
                [('invoice_id.team_id', '=', pp_id.team_id.id),
                 ('full_reconcile_id', '=', False),
                 ('partner_id', '=', partner),
                 ('invoice_id.type', '=', 'out_invoice'),
                 ('invoice_id.state', '=', 'open'),
                 ('account_id.user_type_id.type', '=', 'receivable'),
                 ('date_maturity', '<=', date.date())
                 ])
            if movelines:
                pp_id.black_list = 'blacklist'

    def _compute_credit(self):
        print("JALAN CREDIT Baseeeeeeeeeeeeeeeeeee")
        """ 
            this function to give information over due
            this function to give information remaining credit
        """
        for this in self:
            partner = this.partner_id.id
            team_id = this.team_id.id
            over_due = 'not_overdue'
            credits = 0.0

            # query sale without invoice
            query = """
                select sum(b.price_total) as current_credit
                from sale_order a
                left join sale_order_line b on b.order_id = a.id
                where a.partner_id = %s and a.state in ('sale', 'done','forced_locked')  and a.team_id = %s and 
                NOT EXISTS (SELECT * FROM sale_order_line_invoice_rel WHERE b.id = sale_order_line_invoice_rel.order_line_id)
                and a.id in (select sale_id from stock_picking a 
                             left join stock_location b on a.location_dest_id = b.id 
                             where b.usage = 'customer' and a.state not in ('cancel', 'done','forced_locked') 
                             and a.sale_id is NOT NULL )
            """
            self.env.cr.execute(query, (partner, team_id,))
            result = self.env.cr.dictfetchone()
            if result:
                credits += result['current_credit'] or 0.0


            # add by dion 22 juli 2020, to cover retur
            query = """
                select sum(sm.product_uom_qty * sol.price_unit) as current_credit 
                from stock_move sm
                        left join stock_picking sp on sm.picking_id = sp.id
                        left join sale_order so on sp.sale_id = so.id
                        left join stock_location sl on sp.location_dest_id = sl.id
                        left join sale_order_line sol on sm.sale_line_id = sol.id
                        where sl.usage ='internal' and sp.state in ('done') and sp.partner_id = %s and so.team_id = %s and sp.sale_id is NOT NULL;
            """
            self.env.cr.execute(query, (partner, team_id,))
            result = self.env.cr.dictfetchone()
            if result:
                credits -= result['current_credit'] or 0.0


            # query sale use invoice
            query = """
                select (coalesce(sum(inv.amount_residual),0)) as current_credit 
                from account_move inv where inv.id in (
                select distinct(e.id) as current_credit
                from sale_order a
                left join sale_order_line b on b.order_id = a.id
                left join sale_order_line_invoice_rel c on c.order_line_id = b.id
                left join account_move_line d on c.invoice_line_id = d.id
                left join account_move e on d.move_id = e.id and e.state in ('draft','posted') 
                where a.partner_id = %s and a.state in ('sale', 'done','forced_locked') and a.team_id = %s and e.type = 'out_invoice'
                )
            """
            self.env.cr.execute(query, (partner, team_id,))
            result = self.env.cr.dictfetchone()
            if result:
                credits += result['current_credit'] or 0.0
            # query invoice without sale
            query = """
                select (coalesce(sum(inv.amount_residual),0)) as current_credit 
                from account_move inv where inv.id in (
                    select distinct(a.id)
                    from account_move a
                    left join account_move_line b on a.id = b.move_id
                    left join sale_order_line_invoice_rel c on b.id = c.invoice_line_id
                    where a.partner_id = %s and a.state in ('draft','posted','forced_locked') and a.team_id = %s and c.invoice_line_id = Null and inv.type = 'out_invoice'
                )
            """
            self.env.cr.execute(query, (partner, team_id,))
            result = self.env.cr.dictfetchone()
            if result:
                credits += result['current_credit'] or 0.0
            moveline_obj = self.env['account.move.line'].sudo()
            today_dt = datetime.now().date()

            # Check Over Due
            movelines = moveline_obj.search(
                [('partner_id', '=', partner), ('reconciled', '=', False),
                 ('move_id.type', '=', 'out_invoice'),
                 ('account_id.user_type_id.type', '=', 'receivable'),
                 ('move_id.team_id', '=', team_id), ('move_id.state', '=', 'posted')]
            )
            movelines_over = movelines.filtered(lambda l: l.date_maturity < today_dt)
            
            # Check Over Due without link Invoice
            movelines2 = moveline_obj.search(
                [('partner_id', '=', partner), ('reconciled', '=', False),
                 ('move_id.type', '=', 'out_invoice'),
                 ('account_id.user_type_id.type', '=', 'receivable'),
                 ('payment_id.invoice_ids.team_id', '=', team_id), ('payment_id.state', '=', 'posted')]
            )
            movelines_over_2 = movelines2.filtered(lambda l: l.date_maturity < today_dt)
            # Query payment without invoice
            total_payment = sum(line.amount_residual for line in movelines2)
            
            if movelines_over or movelines_over_2:
                over_due = 'overdue'
            remaining_limit = this.credit_limit - credits - total_payment
            this.update({
                'over_due':over_due,
                'current_credit':credits + total_payment,
                'remaining_limit':remaining_limit
            })

    def btn_update_pricelist(self):
        view_id = self.env.ref('partner_credit_limit.partner_pricelist_view_form').id
        return {
            'name':'Partner Pricelist',
            'view_type':'form',
            'view_mode':'tree',
            'views':[(view_id,'form')],
            'res_model':'partner.pricelist',
            'view_id':view_id,
            'res_id':self.id,
            'type':'ir.actions.act_window',
            'target':'new'
               }
    
    def confirm(self):
        return {'type': 'ir.actions.act_window_close'}