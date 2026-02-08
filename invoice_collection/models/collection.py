from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError,Warning
from datetime import datetime, timedelta
from odoo.tools.misc import formatLang, format_date as odoo_format_date, get_lang
import logging
_logger = logging.getLogger(__name__)

class CollectionActivity(models.Model):
    _name = 'collection.activity'
    _description = 'Collection Activity'
    _inherit = ["approval.matrix.mixin",'mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(string='Name', track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company.id, track_visibility='onchange')
    activity_date = fields.Date(string='Collection Date',required=True,default=datetime.today(), track_visibility='onchange')
    collector_id = fields.Many2one('res.partner', string='Collector',required=True,domain="[('collector','=',True)]", track_visibility='onchange')
    applicant_user_id = fields.Many2one('res.users', string="Applicant", required=True, default=lambda self:self.env.user.id)
    gap_boolean_approve = fields.Boolean('Gap Approved?')

    def unlink(self):
        if any(self.mapped(lambda r:r.state!='draft')):
            raise ValidationError(_("Only can deleting draft Collection Document(s)!"))
        
        return super().unlink()


    show_start = fields.Boolean(compute="_compute_show_start", string="Show Start Button")
    is_user_collector = fields.Boolean(compute="_compute_show_start", string="User Collector")

    def _compute_show_start(self):
        collector_only = self.user_has_groups('invoice_collection.group_collection_collector,!invoice_collection.group_collection_approver') or self.user_has_groups('invoice_collection.group_collection_top_manager')
        # no need loop
        for rec in self:
            res = False
            if rec.state=='ready' and collector_only:
                res = True
            rec.update({
                'show_start':res,
                'is_user_collector':collector_only
            })

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('proposed', 'Proposed'),
        ('ready', 'Ready to Collect'),
        ('collecting', 'Collecting'),
        ('finance_review', 'Finance Review'),
        ('done', 'Done')
    ], string='State',default='draft',required=True, track_visibility='onchange')
    highest_overdue_invoice = fields.Integer(compute='_compute_highest_overdue_invoice', help="Highest Overdue days on invoices", track_visibility='onchange')
    line_ids = fields.One2many('collection.activity.line', 'activity_id', string='Invoices', track_visibility='onchange')
    paid_line_ids = fields.One2many('collection.activity.line', 'activity_id', string='Invoices', track_visibility='onchange',domain=[('invoice_state','in',['paid'])])
    non_paid_line_ids = fields.One2many('collection.activity.line', 'activity_id', string='Invoices', track_visibility='onchange',domain=[('invoice_state','not in',['paid'])])
    journal_ids = fields.Many2many('account.journal',compute='_compute_journal_ids', string='Payments Summary', track_visibility='onchange')
    discount_ids = fields.Many2many('discount.target.support.customer',compute='_compute_discount_ids', string='Discounts', store=True)
    e_tax_ids = fields.One2many('collection.activity.etax', 'activity_id', string='E-Tax')

    def _fetch_next_seq(self):
        return self.env['ir.sequence'].next_by_code('seq.collection.activity')

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            if val.get('name') == False or val.get('name').lower() == 'new':
                val.update({'name':self._fetch_next_seq()})

        return super().create(vals)

    def _compute_journal_ids(self):
        for rec in self:
            rec.journal_ids = rec.line_ids.mapped('journal_ids')

    @api.depends('line_ids')
    def _compute_discount_ids(self):
        for rec in self:
            today = fields.Date.to_string(datetime.now())
            discount_ids = self.env['discount.target.support.customer'].search([('state','=','approved'),('start_date','>=',today),('end_date','<=',today)])
            rec.discount_ids = [(6,0,[disc.id for disc in discount_ids.filtered(lambda r : r.remain_disc > 0)])]

    def _compute_highest_overdue_invoice(self):
        overdues = []
        for rec in self:
            for invoice in rec.line_ids.mapped('invoice_id'):
                overdues.append(invoice.overdue_days)
            max_overdue = 0
            if len(rec.line_ids):
                max_overdue = max(overdues)

            rec.highest_overdue_invoice = max_overdue
            
    
    def reset_follower_and_approvals(self):
        for rec in self:
            followers_partner = []
            for approval in rec.approval_ids:
                for approver in approval.approver_ids:
                    followers_partner.append(approver.partner_id.id)
            rec.message_unsubscribe(partner_ids=followers_partner)
            rec.approval_ids = [(5, 0)]

    def btn_draft(self):
        self.ensure_one()
        self.reset_follower_and_approvals()
        self.state = 'draft'

    def _validate_to_submit(self):
        self.ensure_one()
        # make sure line_ids filled
        if not len(self.line_ids):
            raise UserError(_("Invoice not selected!\nIt's required to continue onto next process!"))

    def btn_submit(self):
        list_partner = self.line_ids.mapped('partner_id')
        if len(list_partner) > 1:
            raise UserError(_("Cannot add more than one partner in one collection"))

        if self.check_gap_date() and self.gap_boolean_approve == False:
            raise UserError(_("Any gap date in list of invoice."))
        else:
            self._validate_to_submit()
            self.checking_approval_matrix(add_approver_as_follower=True, data={'state':'waiting_approval'})
            self.message_subscribe(partner_ids=self.collector_id.ids)
    

    def check_gap_date(self):
        gap = False
        date = ''
        for rec in self.line_ids:
            if isinstance(date, str):
                partner_id = rec.partner_id.id
                # invoice_ids = self.env['account.move'].search([('type','=','out_invoice'),('partner_id','=',partner_id),('state','not in',['draft','cancel'])])
                # for each in invoice_ids:
                #     if each.id == rec.invoice_id.id
                date = rec.invoice_date
            else:
                # if partner_id == rec.partner_id.id: # FIXME : Remove line as request check do not check partner for gap
                gap_date = date-rec.invoice_date
                if gap_date.days > 1:
                    gap = True
                else:
                    date = rec.invoice_date
        return gap


    def action_approve(self):
        self.state = 'approved'

    def btn_approve(self):
        self.ensure_one()
        self.approving_matrix(post_action='action_approve')

    def btn_reject(self):
        self.ensure_one()
        self.rejecting_matrix()
        self.state = 'rejected'
    
    def btn_proposed(self):
        self.state = 'proposed'

    def open_post_message_wizard(self):
        self.ensure_one()
        non_check_1 = []
        for line in self.line_ids.filtered(lambda r: r.check_1 == False):
            non_check_1.append(line.invoice_id.display_name)

        joined_non_check_1=''
        if len(non_check_1) > 0:
            joined_non_check_1 =', '.join(non_check_1)
            
            message = "<h4>"+ joined_non_check_1 +" document not handover to collector, are you sure?</h4>"
            form = self.env.ref('message_action_wizard.message_action_wizard_form_view')
            context = dict(self.env.context or {})
            context.update(
                {
                    'default_res_model_id':self.env['ir.model'].with_user(1).search([('model','=',self._name)]).id,
                    'default_res_id':self.id,
                    'default_messages':message,
                    "default_action_confirm": "btn_post"
                })
            res = {
                'name': "%s - %s" % (_('Confirmation Message'), self.name),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'message.action.wizard',
                'view_id': form.id,
                'type': 'ir.actions.act_window',
                'context': context,
                'target': 'new'
            }
            return res
        else:
            self.btn_post()

    def btn_post(self):
        if self.e_tax_ids:
            for rec in self.e_tax_ids:
                rec.doc_status = 'on_collector'
                rec.post()
        self.state = 'ready'
        return{
            'effect': {
                'fadeout': 'fast',
                'message': _("Collection Posted!"),
                # 'img_url': '/sanqua_sale_flow/static/src/img/wow.png',
                'type': 'rainbow_man',
            }
        }

    def _validate_to_review(self):
        self.ensure_one()
        # make sure all has payment_status
        if any(self.line_ids.mapped(lambda r:r.payment_status==False)):
            not_defined = self.line_ids.filtered(lambda r:r.payment_status==False)
            raise UserError(_("Please fill payment_status at %s!") % (",".join(not_defined.mapped('invoice_id.display_name'))))
    
    def btn_to_review(self):
        self.ensure_one()
        self._validate_to_review()
        self.state = 'finance_review'

    def _valid_to_done(self):
        self.ensure_one()
        if any(self.line_ids.mapped(lambda r:r.doc_status==False)):
            raise UserError(_("Please check %s, it's Required!") % (self.line_ids._fields.get('doc_status').string, ))

        if any(self.line_ids.mapped(lambda r:r.doc_status=='not_returned')):
            if self.user_has_groups('invoice_collection.group_collection_top_manager'):
                for line in self.line_ids:
                    line.approved_by = self.env.user
            else:
                raise UserError(_("There's document wich not returned. Approval needed by manager!"))

    def btn_done(self):
        self._valid_to_done()
        self.state = 'done'

    def btn_start(self):
        self.ensure_one()
        self.state = 'collecting'

    def btn_add_invoice(self):
        view_id = self.env.ref('invoice_collection.collection_activitiy_line_view_form_add_invoice').id
        return {
            'name':'Collection Activity Line',
            'view_type':'form',
            'view_mode':'tree',
            'views':[(view_id,'form')],
            'res_model':'collection.activity.line',
            'view_id':view_id,
            'type':'ir.actions.act_window',
            'context':{'default_activity_id':self.id},
            'target':'new'
               }

    def btn_add_unpaid_invoice(self):
        context = dict(self.env.context or {})
        context.update({
                'default_activity_id':self.id,
                'invoice_payment_state':['not_paid','in_payment'],
                'default_check_1':True
                })
        view_id = self.env.ref('invoice_collection.collection_activitiy_line_view_form_add_invoice').id
        return {
            'name':'Collection Activity Line',
            'view_type':'form',
            'view_mode':'tree',
            'views':[(view_id,'form')],
            'res_model':'collection.activity.line',
            'view_id':view_id,
            'type':'ir.actions.act_window',
            'target':'new',
            'context':context
            }

    def btn_add_paid_invoice(self):
        context = dict(self.env.context or {})
        context.update({
                'default_activity_id':self.id,
                'invoice_payment_state':['paid'],
                'default_check_1':True
                })
        view_id = self.env.ref('invoice_collection.collection_activitiy_line_view_form_add_invoice').id
        return {
            'name':'Collection Activity Line',
            'view_type':'form',
            'view_mode': 'form',
            'res_model':'collection.activity.line',
            'view_id':view_id,
            'context':context,
            'type':'ir.actions.act_window',
            'target':'new',
            }

    def btn_add_tax_ids(self):
        context = dict(self.env.context or {})
        context.update({
                'activity_id':self.id
                })
        view_id = self.env.ref('invoice_collection.collection_activity_etax_wizard_view_form_add_invoice').id
        return {
            'name':'E-Tax Invoice',
            'view_type':'form',
            'view_mode': 'form',
            'res_model':'collection.activity.etax.wizard',
            'view_id':view_id,
            'context':context,
            'type':'ir.actions.act_window',
            'target':'new',
            }

    def btn_add_invoice_collection_ids(self):
        context = dict(self.env.context or {})
        context.update({
                'default_activity_id':self.id
                })
        view_id = self.env.ref('invoice_collection.invoice_collection_wizard_view_form').id
        return {
            'name':'Invoice Collections',
            'view_type':'form',
            'view_mode': 'form',
            'res_model':'invoice.collection.wizard',
            'view_id':view_id,
            'context':context,
            'type':'ir.actions.act_window',
            'target':'new',
            }

class CollectionActivityLine(models.Model):
    _name = 'collection.activity.line'
    _description = 'Collection Activity Line'

    activity_id = fields.Many2one('collection.activity', string='Activity',ondelete="cascade", onupdate="cascade",required=True, track_visibility='onchange')
    invoice_id = fields.Many2one('account.move', string='Invoice',required=True, track_visibility='onchange', domain=[('type','=','out_invoice'),('state','not in',['draft','cancel'])])
    partner_id = fields.Many2one('res.partner',string='Customer', track_visibility='onchange')
    currency_id = fields.Many2one(related='invoice_id.currency_id', string='Currency', readonly=True, track_visibility='onchange')
    amount_total = fields.Monetary(related='invoice_id.amount_total', string='Amount Total', readonly=True, track_visibility='onchange')
    invoice_date = fields.Date(related='invoice_id.invoice_date',string='Date')
    invoice_origin = fields.Char(related='invoice_id.invoice_origin',string='Delivery Order')
    amount_residual = fields.Monetary(compute='_compute_amount_residual', string='Amount Residual',store=True, track_visibility='onchange')
    pay_amount = fields.Monetary(string='Pay Amount',track_visibility='onchange')
    attachment = fields.Binary(string='Attachment', track_visibility='onchange')
    payment_status = fields.Selection([
        ('paid', 'Paid'),
        ('partial_paid', 'Partial Paid'),
        ('unpaid', 'Unpaid'),
        ('tukar_faktur', 'Tukar Faktur')
    ], string='Payment Status', track_visibility='onchange')
    doc_status = fields.Selection([
        ('returned', 'Returned'),
        ('not_returned', 'Not Returned'),
    ], string='Doc Status',track_visibility='onchange')
    payment_ids = fields.One2many('collection.activity.line.payment', 'line_id', string='Payments', track_visibility='onchange')
    sum_payment_amount = fields.Monetary(compute='_compute_sum_payment_amount', string='Payment Amount', track_visibility='onchange')
    journal_ids = fields.Many2many('account.journal',compute='_compute_journal_ids', string='Payment Journals', track_visibility='onchange')
    company_id = fields.Many2one(related='activity_id.company_id', string='Company',store=True, track_visibility='onchange')
    state = fields.Selection(related='activity_id.state', string='State', readonly=True)
    invoice_state = fields.Selection([
        ('not_paid', 'Unpaid'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
    ],compute='_compute_invoice_state',store=True)
    check_1 = fields.Boolean(string='Handovered', help="Is Invoice handovered to collector from accountant.")
    notes = fields.Text(string='Notes')
    # picking_ids = fields.Many2many('stock.picking', string='Delivery Orders',compute='_compute_picking_ids')
    approved_by = fields.Many2one('res.users', string='Approved By')

    _sql_constraints = [
        ('invoice_uniq', 'unique (activity_id,invoice_id)', 'Cannot fill same Collection and Invoice !'),
    ]
    
    @api.depends('invoice_id')
    def _compute_invoice_state(self):
        for rec in self:
            rec.invoice_state = rec.invoice_id.invoice_payment_state if rec.invoice_id else False

    # @api.depends('invoice_id')
    # def _compute_picking_ids(self):
    #     for rec in self:
    #         rec.picking_ids = [(6,0,rec.invoice_id.mapped(lambda self: self.invoice_line_ids.mapped(lambda r: r.sale_line_ids.mapped(lambda rr: rr.move_ids.mapped('picking_id').filtered(lambda p: p.state == 'done' and p.picking_type_id.code == 'outgoing')))).ids)] if rec.invoice_id else False
    
            
    @api.constrains('pay_amount','payment_status')
    def _constrains_payment_status(self):
        for rec in self:
            if rec.activity_id.state in ['collecting','finance_review','done']:
                if rec.payment_status == 'paid':
                    if float(rec.amount_residual) != float(rec.pay_amount):
                        raise UserError(_('If status "Paid" Payment amount should be same as residual amount!'))
                elif rec.payment_status == 'unpaid':
                    if len(rec.payment_ids) > 0:
                        raise UserError(_('If status "Unpaid" then payment line must blank!\nPlease Check!'))
                elif rec.payment_status == 'partial_paid':
                    if len(rec.payment_ids) == 0 or float(rec.pay_amount) <= 0.0:
                        raise UserError(_('If status "Partial Paid", At least required to fill 1 Payment.'))
                elif rec.payment_status == 'tukar_faktur':
                    if len(rec.payment_ids) > 0:
                        raise UserError(_('If status "Tukar Faktur" then payment line must blank!\nPlease Check!'))
                    
                    if not rec.attachment:
                        raise UserError(_("If payment status == 'Tukar Faktur' then Attachment is required"))

    def name_get(self):
        result = []
        for pp in self:
            result.append((pp.id, pp.invoice_id.name))
        return result

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            if self._context.get('invoice_payment_state'):
                return {'domain':{'invoice_id':[('state','not in',['draft','cancel']),('invoice_payment_state','in',self._context.get('invoice_payment_state')),('partner_id','=',self.partner_id.id),('type', '=', 'out_invoice')]}}
            else:
                return {'domain':{'invoice_id':[('partner_id','=',self.partner_id.id),('state','not in',['draft','cancel']),('type', '=', 'out_invoice')]}}
        else:
            return {'domain':{'invoice_id':[('type','=','out_invoice'),('state','not in',['draft','cancel'])]}}

    def _compute_journal_ids(self):
        for rec in self:
            rec.journal_ids = rec.payment_ids.mapped('journal_id')
    
    def _compute_sum_payment_amount(self):
        for rec in self:
            rec.sum_payment_amount = sum(rec.payment_ids.mapped('amount'))

    @api.onchange('invoice_id')
    def _onchange_invoice_id(self):
        if self.invoice_id.id:
            self.env['invoice.collection.wizard'].check_allowed_invoice(self.invoice_id)
        if self.invoice_id.id and not self.partner_id.id:
            self.partner_id = self.invoice_id.partner_id.id

    @api.depends('invoice_id')
    def _compute_amount_residual(self):
        for rec in self:
            rec.amount_residual = rec.invoice_id.amount_residual

    @api.constrains('payment_ids','pay_amount')
    def _constrains_payment_ids(self):
        self.validating_payment()
    
    def validating_payment(self):
        
        for rec in self:
            if rec.pay_amount != rec.sum_payment_amount:
                raise UserError(_('Payment Amount not matching.'))
    
    def btn_update_status(self):
        view_id = self.env.ref('invoice_collection.collection_activitiy_line_view_form_update_status').id
        return {
            'name':'Collection Activity Line',
            'view_type':'form',
            'view_mode':'tree',
            'views':[(view_id,'form')],
            'res_model':'collection.activity.line',
            'view_id':view_id,
            'res_id':self.id,
            'type':'ir.actions.act_window',
            'target':'new'
               }

    def confirm(self):
        self._constrains_payment_status()
        return {'type': 'ir.actions.act_window_close'}

    def btn_delete(self):
        self.unlink()
        
class CollectionActivityLinePayment(models.Model):
    _name = 'collection.activity.line.payment'
    _description = 'Collection Activity Line Payment'

    line_id = fields.Many2one('collection.activity.line', string='Invoice',required=True, ondelete='cascade', onupdate='cascade', track_visibility='onchange')
    
    partner_id = fields.Many2one(related='line_id.invoice_id.partner_id', string='')
    allowed_discount_ids = fields.Many2many(related='line_id.activity_id.discount_ids', string='Allowed Discount')
    
    activity_id = fields.Many2one('collection.activity', related='line_id.activity_id', string='Activity',store=True, track_visibility='onchange')
    journal_id = fields.Many2one('account.journal', string='Journal',domain="[('type','in',['bank','cash'])]", track_visibility='onchange')
    currency_id = fields.Many2one(related='line_id.currency_id', string='Currency', track_visibility='onchange')
    amount = fields.Monetary(string='Amount',required=True, track_visibility='onchange')
    company_id = fields.Many2one(related='activity_id.company_id', string='Company',store=True, track_visibility='onchange')
    discount_id = fields.Many2one('discount.target.support.customer', string='Discount', track_visibility='onchange')
    state = fields.Selection(related='activity_id.state', readonly=True)
    
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, rec.line_id.invoice_id.name+' - '+' '+rec.journal_id.name+' - '+' '+ str(formatLang(self.env, rec.amount))))
        return result

    def validating_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise UserError(_('Amount not vaid'))

    @api.constrains('amount')
    def _constrains_amount(self):
        self.validating_amount()