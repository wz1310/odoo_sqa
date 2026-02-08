from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.api import SUPERUSER_ID
import logging
_logger = logging.getLogger(__name__)

from odoo.addons.sanqua_discount_target_support.helpers import amount_to_text,\
    format_local_currency,\
    format_local_datetime

class DiscountTargetSupportCustomer(models.Model):
    _name = "discount.target.support.customer"
    _description = "Discount Target Support Customer"
    _inherit = ["discount.target.support.mixin","approval.matrix.mixin",'mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='No. Document')
    master_id = fields.Many2one('discount.target.support.master', string='Discount Master')
    allowed_partner_ids = fields.Many2many('res.partner', string="Allowed Partner", compute="_compute_allowed_partner_ids")

    partner_id = fields.Many2one('res.partner', required=True, string='Customer')
    target_qty = fields.Float(string='Target Qty', digits="Product Uom")
    disc_type = fields.Selection(related="master_id.disc_type", string='Type',store=False,readonly=True)
    discount = fields.Float(string='Discount', digits="Unit Price", compute="_compute_discount", store=True, inverse="_inverse_true")
    remain_disc = fields.Float(compute='_compute_remain_disc', string="Remaining Discount")
    disc_usage = fields.Float(compute='_compute_disc_usage',string='Usage Discount')
    usage_ids = fields.One2many('discount.target.support.customer.usage', 'disc_customer_id', string='Discount Usage')
    realization_qty = fields.Float(string='Qty Realization', compute='_compute_realization_qty')
    discount_qty = fields.Float(string='Disc Qty', compute="_compute_discount", store=True, inverse="_inverse_true")
    realization_date_start = fields.Date(string='Date Start',required=True)
    realization_date_end = fields.Date(string='Date End',required=True)
    journal_id = fields.Many2one('account.journal', string='Journal')
    debit_account_id = fields.Many2one('account.account', string='Debit Account')
    credit_account_id = fields.Many2one('account.account', string='Credit Account')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('reject', 'Reject')
    ], string='State',default='draft',required=True)

    move_entry_id = fields.Many2one('account.move', domain=[('type','=','entry')], string="Move Entry")
    sale_report_ids = fields.Many2many('sale.report', string='Sale Report',compute='_compute_sale_report_ids')
    line_ids = fields.One2many('discount.target.support.customer.line', 'discount_id', string='Lines')
    tax_debit_account_id = fields.Many2one('account.account', string='Tax Debit Account')
    tax_credit_account_id = fields.Many2one('account.account', string='Tax Credit Account')
    target_type = fields.Char(string='Target Type')
    description = fields.Char('Description')
    

    _sql_constraints = [
        ('name_unique', 'unique (name)', _('Name already used')),
    ]

    def _inverse_true(self):
        return True

    @api.depends('line_ids.discount_amount')
    def _compute_discount(self):
        for rec in self:
            res_amount = 0.0
            res_qty = 0.0
            if len(rec.line_ids):
                res_amount = sum(rec.line_ids.mapped(lambda r:r.discount_amount))
                res_qty = sum(rec.line_ids.mapped(lambda r:r.discount_qty))
            rec.update({
                'discount':res_amount,
                'discount_qty':res_qty
            })
    
    def _validating_discount(self):
        for rec in self:
            if rec.discount<=0:
                raise UserError(_("Discount must greater than 0.0"))

    def _compute_sale_report_ids(self):
        for rec in self:
            rec.sale_report_ids = False
            query = """
                SELECT * FROM sale_report WHERE team_id = %s and partner_id = %s and date >= %s and date <= %s and company_id = %s;
            """
            rec.env.cr.execute(query, (rec.team_id.id,rec.partner_id.id,rec.start_date,rec.end_date,self.env.company.id))
            ids = [row[0] for row in rec.env.cr.fetchall()]
            if ids:
                rec.sale_report_ids = [(6,0,ids)]
    
    def btn_fetch_sale_report(self):
        line_ids = [(5,)]
        for line in self.sale_report_ids.mapped('product_id').filtered(lambda r:r.type=='product'):
            sale_reports = self.sale_report_ids.filtered(lambda r: r.product_id.id == line.id)
            line_ids.append((0,0, {
                'discount_id':self.id,
                'sale_report_id':False,
                'product_id':line.id,
                'qty_order': sum([report.product_uom_qty for report in sale_reports]),
                'qty_delivered': sum([report.qty_delivered for report in sale_reports]),
                'price_delivered': sum([report.untaxed_amount_to_invoice for report in sale_reports]),
                'price_subtotal': sum([report.price_subtotal for report in sale_reports])
            }))
        self.line_ids = line_ids
    
    @api.depends('partner_id')
    def _compute_realization_qty(self):
        # sale_id = self.env['sale.order'].search([('partner_id','=', self.partner_id.id),('date_order','>=',self.realization_date_start),('date_order','<=',self.realization_date_end),('state','in',['sale','done'])])
        sale_id = self.env['sale.order'].search([('partner_id','=', self.partner_id.id),('date_order','>=',self.start_date),('date_order','<=',self.end_date),('state','in',['sale','done'])])
        self.realization_qty = sum([line.qty_delivered for line in sale_id.order_line])
    
    @api.depends('master_id')
    def _compute_allowed_partner_ids(self):
        for rec in self:
            res = self.env['res.partner']
            if rec.master_id.id:
                res = rec.master_id.partner_ids
            rec.allowed_partner_ids = res


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('seq.discount.target.support.customer.code')
        return super(DiscountTargetSupportCustomer, self).create(vals_list)

    def _validating_report(self):
        if not len(self.sale_report_ids):
            raise UserError(_("Can't Submit With Empty Report!"))
        if self.discount<=0:
            raise UserError(_("TOtal Discount must be greater than 0.0"))
        if self.discount_qty<=0:
            raise UserError(_("TOtal Discount Qty must be greater than 0.0"))


    def btn_submit(self):
        self.checking_approval_matrix()
        self._validating_report()
        self.state = 'waiting_approval'

    def action_approve(self):
        #new_account_move = self.create_journal_entries()
        self.update({
            #'move_entry_id':new_account_move,
            'state':'approved'
        })

    def btn_approve(self):
        self.approving_matrix(post_action='action_approve')
            

    def btn_draft(self):
        self.state = 'draft'

    def btn_reject(self):
        self.rejecting_matrix()
        self.state = 'reject'

    def _prepare_journal_entry_lines(self):
        self.ensure_one()
        #amount_discount = round(self.discount / 1.1)
        amount_discount = self.discount - ((self.discount * 10)/100)
        #amount_tax = round(amount_discount * 10.0 / 100.0)
        amount_tax = round(self.discount * 10.0 / 100.0)
        return [
            (0,0,{
                'account_id':self.debit_account_id.id,
                'partner_id':self.partner_id.id,
                'name':self.display_name + ' debit',
                'debit':amount_discount,#1.530.000
            }),
            # (0,0,{
            #     'account_id':self.tax_credit_account_id.id,
            #     'partner_id':self.partner_id.id,
            #     'name':self.display_name + ' credit',
            #     'credit':amount_tax,
            # }),
            (0,0,{
                'account_id':self.tax_debit_account_id.id,
                'partner_id':self.partner_id.id,
                'name':self.display_name + ' debit',
                'debit':amount_tax,##170.000
            }),

            (0,0,{
                'account_id':self.credit_account_id.id,
                'partner_id':self.partner_id.id,
                'name':self.display_name + ' credit',
                'credit':amount_discount+amount_tax,
            }),
            
        ]

    def create_journal_entries(self):
        data = {
                'ref':self.display_name,
                'journal_id':self.journal_id.id,
                'company_id':self.company_id.id,
                'team_id':self.team_id.id,
                'line_ids':self._prepare_journal_entry_lines()
        }
        
        Entry = self.env['account.move'].with_context({'default_type': 'entry'}).with_user(SUPERUSER_ID)

        NewEntry = Entry.create(data)

        return NewEntry

 
    @api.onchange('master_id')
    def _onchange_master_id(self):
        self.partner_id = False
        self.target_type = self.master_id.target_type

    @api.depends('disc_usage')
    def _compute_remain_disc(self):
        for s in self:
            s.remain_disc = s.discount - s.disc_usage
    
    @api.depends('usage_ids')
    def _compute_disc_usage(self):
        for s in self:
            s.disc_usage = sum([usage.disc_usage for usage in s.usage_ids])

    def get_amount_to_text(self,amount):
        return amount_to_text(amount)

class DiscountTargetSupportCustomerUsage(models.Model):
    _name = "discount.target.support.customer.usage"
    _description = "Discount Target Support Customer Usage"

    disc_customer_id = fields.Many2one('discount.target.support.customer', string='Discount Customer')
    settlement_request_number = fields.Char('Settlement Request')
    settlement_request_date = fields.Date('SR Date')
    invoice_id = fields.Many2one('account.move','Invoice')
    payment_id = fields.Many2one('account.payment', string='Payment')
    disc_usage = fields.Float(string="Discount")


class DiscountTargetSupportCustomerLine(models.Model):
    _name = "discount.target.support.customer.line"
    _description = "Discount Target Support Customer Line"


    discount_id = fields.Many2one('discount.target.support.customer', string='Discount Support Customer',required=False)
    team_id = fields.Many2one(related='discount_id.master_id.team_id')

    sale_report_id = fields.Many2one('sale.report', string='Report')
    product_id = fields.Many2one('product.product',string='Product')
    qty_order = fields.Float(string='Order Qty')
    qty_delivered = fields.Float(string='Delivered Qty')
    price_subtotal = fields.Float(string='Price Subtotal')
    price_delivered = fields.Float(string="Price Delivered")

    target_qty = fields.Float(string='Target Qty', digits="Product Unit Of Measure")
    target_amount = fields.Float(string='Target Amount')

    discount_amount = fields.Float(string='Discount Amount')
    discount_qty = fields.Float(string='Discount Qty', digits="Product Unit Of Measure")
    company_id = fields.Many2one(related='discount_id.company_id', string='Company')