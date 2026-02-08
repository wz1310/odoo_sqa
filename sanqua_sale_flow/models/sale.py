# -*- coding: utf-8 -*-
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import UserError,ValidationError,RedirectWarning,AccessError

import logging
_logger = logging.getLogger(__name__)

import xml.etree as etr
import xml.etree.ElementTree as ET
from ast import literal_eval
import re

import datetime

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    pricelist_id = fields.Many2one(
        'product.pricelist', string='Pricelist', check_company=True,  # Unrequired company
        required=False, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="If you change the pricelist, only newly added lines will be affected.")
    interco_master = fields.Boolean(default=False, string="Intercompany Master Order")

    plant_id = fields.Many2one('res.company', string="Plant", required=False, ondelete="restrict", onupdate="restrict", track_visibility="onchange", check_company=False, context={'all_companies':True})
    vehicle_model_id = fields.Many2one('fleet.vehicle.model', string="Vehicle Model", required=False, ondelete="restrict", onupdate="restrict", track_visibility="onchange")
    order_pickup_method_id = fields.Many2one('order.pickup.method', string="Pickup Method")
    partner_can_direct_pickup = fields.Boolean(string="Customer Can Direct Pickup", track_visibility="onchange")
    direct_pickup_reduction_amount = fields.Monetary(string="Reduction Amount", help="When Customer Picking Up Directly, will reducing cost of deliver order and will be generated as discount on Sales Order")

    team_id = fields.Many2one('crm.team', string="Division", required=False, default=False)

    partner_pricelist_ids = fields.One2many('partner.pricelist', compute="_compute_partner_pricelist_ids", readonly=True)
    partner_pricelist_team_id = fields.Many2one('partner.pricelist', compute="_compute_partner_pricelist_team_id", store=True)
    overdue_invoice_ids = fields.Many2many('account.move',compute='_compute_overdue_invoice_ids')
    # overdue_invoice_ids = fields.Many2many('account.move', default=_domain_odue)

    limit_approval_state = fields.Selection([('draft','draft'), ('need_approval_request','Need Approval Request'), ('need_approval','Need Approval'), ('approved','Approved'), ('rejected','Rejected')], default="draft", copy=False, track_visibility="onchange")

    status_so = fields.Selection([('0', 'Normal'), ('1', 'Overdue'), ('2', 'Overlimit'), ('3', 'Overdue & Overlimit'), 
                    ('4', 'Blacklist')])

    SALE_STATE = [
        ('draft', 'Sales Order'),
        ('sent', 'Sales Order Sent'),
        ('sale', 'Order Confirmation'),
        ('done', 'Locked'),
        ('forced_locked','F Locked'),
        ('cancel', 'Cancelled'),
    ]
    state = fields.Selection(SALE_STATE, string="State", default="draft")

    origin_interco_order_id = fields.Many2one('sale.order', string="Original Sale Order", help="Original Intercompany Procurement Order to Customer SaleOrder", compute="_compute_origin_interco_order_id")

    sale_mix_ids = fields.Many2many('sale.order', 'sale_order_mix_rel', 'sale_order_id', 'mix_id', string="SO Mix Ref.")

    discount_changed = fields.Boolean(compute='_compute_discount_changed')

    order_priority = fields.Selection([
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
        ('mix', 'Mix')
    ], string='SO Priority',required=True,default='normal')

    internal_sale_notes = fields.Text()
    
    overlimit_value = fields.Monetary(compute='_compute_overlimit_value')

    priority_type = fields.Selection([('normal','NORMAL'), ('urgent','URGENT'), ('pending','PENDING')], default="normal", required=True)
    blacklist_partner = fields.Boolean(compute='_compute_blacklist_partner', string='Blacklist',default=False,store=True)

    can_cancel_approved = fields.Boolean(compute="_compute_can_cancel_approved", string="Is Active User Can Canceling Approved Order")

    credit_limit_value = fields.Monetary(compute='_compute_credit_limit_value', store=True, string="Credit Limit Value")
    user_id = fields.Many2one('res.users', string="Salesperson", compute="_compute_user_pricelist", store=True)
    allowed_company_ids = fields.Many2many('res.company', 'sale_order_allowed_company_rel', 'sale_order_id', 'allowed_company_id', compute="_compute_allowed_company_ids", store=True, string="Allowed Companies")

    commitment_date_mask = fields.Date('Delivery Date', default=(datetime.datetime.now().date())+datetime.timedelta(days=1))
    date_order_mask = fields.Date('Order Date', default=(datetime.datetime.now().date()))

    total_qty = fields.Float('Total Quantity', compute='_compute_total_qty')
    total_delivered_qty = fields.Float('Delivered Qty', compute='_compute_total_delivered_qty')
    interco_ref_picking_ids = fields.Many2many('stock.picking',compute='_compute_interco_ref_picking_ids', string='Interco Ref Picking', search="_search_interco_ref_picking_ids")
    validity_date = fields.Date(
        string='Expiration', required=False,  
        states={'draft': [('readonly', False)]})

    analytic_account_id = fields.Many2one('account.analytic.account', compute='_compute_analytic_account_id', string='Analytic Account')
    
    @api.depends('team_id')
    def _compute_analytic_account_id(self):
        for rec in self:
            if rec.team_id:
                rec.analytic_account_id = rec.team_id.analytic_account_id
            else:
                rec.analytic_account_id = False

    def _search_interco_ref_picking_ids(self, operator, value):
        picking = self.env['stock.picking'].search([('doc_name',operator,value)])
        so = picking.mapped('sale_id')
        return [('id','in',so.ids)]

    @api.model
    def search_interco_ref_picking_ids(self, operator, value):
        return self._search_interco_ref_picking_ids(operator, value)

    @api.constrains('validity_date')
    def _constrains_validity_date(self):
        for rec in self:
            if rec.validity_date == False:                
                if rec.auto_purchase_order_id:
                    if rec.auto_purchase_order_id.validity_date:
                        rec.validity_date = rec.auto_purchase_order_id.validity_date
                    else:
                        rec.validity_date = rec.auto_purchase_order_id.validity_so_date
                else:
                    rec.validity_date = datetime.datetime.now() + datetime.timedelta(days=2)
    
    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        for rec in self.filtered(lambda r:r.order_id.interco_master):
            if not rec.order_id.warehouse_id:
                raise UserError(_('Please fill the warehouse before input data in order line'))
        return res

    def _read(self, fields):
        return super(SaleOrder, self.sudo())._read(fields)
        
    
    @api.depends('auto_purchase_order_id')
    def _compute_interco_ref_picking_ids(self):
        for rec in self:
            rec.interco_ref_picking_ids = rec.auto_purchase_order_id.sudo().interco_ref_picking_ids.ids if rec.auto_purchase_order_id else False

    @api.depends('order_line.product_uom_qty')
    def _compute_total_qty(self):
        for rec in self:
            rec.total_qty = sum(rec.order_line.mapped('product_uom_qty'))

    @api.depends('order_line.qty_delivered')
    def _compute_total_delivered_qty(self):
        for rec in self:
            rec.total_delivered_qty = sum(rec.order_line.mapped('qty_delivered'))

    @api.onchange('commitment_date_mask')
    def _onchange_commitment_date_mask(self):
        self.ensure_one()
        date = self.commitment_date_mask
        if date:
            format_date = datetime.datetime(date.year, date.month, date.day, 23, 59, 59) + datetime.timedelta(hours=-7)
            self.commitment_date = format_date
            self.validity_date = format_date + datetime.timedelta(days=1)
            if self.auto_purchase_order_id:
                self.validity_date = self.auto_purchase_order_id.validity_date

    @api.onchange('date_order_mask')
    def _onchange_date_order_mask(self):
        self.ensure_one()
        date = self.date_order_mask
        if date:
            format_date = datetime.datetime(date.year, date.month, date.day, 23, 59, 59) + datetime.timedelta(hours=-7)
            self.date_order = format_date

    @api.depends('company_id','plant_id','picking_ids.plant_id')
    def _compute_allowed_company_ids(self):
        for rec in self:
            rec.update({
                'allowed_company_ids':[(6,0,rec.sudo().company_id.ids+rec.sudo().plant_id.ids+rec.picking_ids.sudo().mapped('plant_id').ids)]
            })

    @api.depends('partner_pricelist_team_id')
    def _compute_credit_limit_value(self):
        for rec in self:
            res = 0.0
            if rec.partner_pricelist_team_id.id:
                res = rec.partner_pricelist_team_id.remaining_limit
            rec.credit_limit_value = res


    @api.depends('partner_id')
    def _compute_partner_pricelist_ids(self):
        for rec in self:
            # self.env.cr.execute(""" SELECT * FROM "partner_pricelist" WHERE partner_id="""+str(int(rec.partner_id.id))+""" AND team_id="""+str(int(rec.team_id.id))+""" """)
            # sql  = self.env.cr.fetchall()
            # rec.partner_pricelist_ids = [x[0] for x in sql]
            rec.partner_pricelist_ids = rec.partner_id.partner_pricelist_ids
            # penambahan pengecekan status ovdue & ovlimit pada SO 20 Des 2022
            self._set_status_so()
            # perubahan orm->query ketika rubah customer
            # self.env.cr.execute(""" SELECT * FROM "partner_pricelist" WHERE partner_id="""+str(int(rec.partner_id.id))+""" AND team_id="""+str(int(rec.team_id.id))+""" """)
            # sql  = self.env.cr.fetchall()
            # rec.partner_pricelist_ids = [x[0] for x in sql]

    @api.model
    def create(self,vals):
        if not vals.get('partner_pricelist_team_id'):
            if vals.get('sale_agreement_id'):
                # if from sale agreement
                agreement = self.env['sale.agreement'].browse(int(vals.get('sale_agreement_id')))
                if not len(agreement):
                    raise ValidationError(_("No Agreement Found!"))
                pricelist = agreement.partner_id.partner_pricelist_ids.filtered(lambda r:r.team_id.id==agreement.team_id.id)
                vals.update({'partner_pricelist_team_id':pricelist.id})

        if vals.get('partner_pricelist_team_id') and not vals.get('pricelist_id'):
            price = self.env['partner.pricelist'].browse((int(vals.get('partner_pricelist_team_id'))))
            if price:
                price = price.pricelist_id
            if vals.get('partner_id'):
                partner = self.env['res.partner'].browse(int(vals.get('partner_id')))
                if len(partner.ref_company_ids):
                    # if partner is a company
                    if partner.property_product_pricelist:
                        price = partner.property_product_pricelist
            
            
            if len(price):
                vals.update({'pricelist_id':price.id})
        sup = super().create(vals)
        if sup.pricelist_id.id==False and vals.get('pricelist_id'):
            sup.sudo().update({
                'pricelist_id':vals.get('pricelist_id')
            })
        # if sup.auto_purchase_order_id:
        #     sup.validity_date = sup.auto_purchase_order_id.validity_date
        sup._set_status_so()
        return sup

    @api.depends('partner_pricelist_team_id')
    def _compute_user_pricelist(self):
        for rec in self:
            if rec.partner_pricelist_team_id.id:
                user_id = rec.partner_pricelist_team_id.user_id.id
                rec.update({
                    'user_id':user_id,
                })
            else:
                rec.update({
                    'user_id':False,
                })

    
    
    def _compute_can_cancel_approved(self):
        for rec in self:
            rec.can_cancel_approved = self.env.user.id in rec.approvers_user_ids.ids

    
    
    @api.depends('team_id','partner_id')
    def _compute_blacklist_partner(self):
        for rec in self:
            rec.blacklist_partner = False
            pricelist = rec.partner_id.sudo().sudo().sudo().partner_pricelist_ids.filtered(lambda r:r.team_id.id==rec.team_id.id).sorted('id', reverse=True)
            if len(pricelist)>0:
                if pricelist.black_list == 'blacklist':
                    rec.blacklist_partner = True

    @api.constrains('blacklist_partner')
    def _constrains_blacklist_partner(self):
        for rec in self:
            rec.check_blacklist()

    def check_blacklist(self):
        if self.blacklist_partner == True:
                raise UserError(_("Cannot process SO with blacklist customer %s.")%(self.partner_id.display_name))

    def name_get(self):
        res = []
        if self._context.get('show_division'):
            for rec in self:
                name = "%s | %s | %s | %s" % (rec.name, rec.team_id.display_name, rec.date_order_mask, sum(rec.order_line.mapped('product_uom_qty')),)
                res += [(rec.id, name)]
        else:
            res = super().name_get()
        return res
    

    def display_name(self):
        if self._context.get('show_division'):
            for rec in self:
                rec.display_name = "%s | %s | %s | %s" % (rec.name, rec.team_id.display_name, rec.date_order_mask, sum(rec.order_line.mapped('product_uom_qty')), )
        else:
            super().display_name()
    
    @api.depends('partner_id')
    def _compute_overlimit_value(self):
        for rec in self:
            overlimit_val = 0
            if rec.partner_id and not rec.partner_id.ref_company_ids.ids:
                for price in rec.partner_id.sudo().partner_pricelist_ids:
                    if price.team_id.id == rec.team_id.id:
                        if (price.current_credit + rec.amount_total) > price.credit_limit:
                            overlimit_val = (price.current_credit + rec.amount_total) - price.credit_limit
                # # prubahan penambahan filter team_id pada over limit
                # for price in rec.partner_id.sudo().partner_pricelist_ids.filtered(lambda r:r.team_id.id==rec.team_id.id):
                #     if (price.current_credit + rec.amount_total) > price.credit_limit:
                #         overlimit_val = (price.current_credit + rec.amount_total) - price.credit_limit
            rec.overlimit_value = overlimit_val

    @api.depends('order_line.discount')
    def _compute_discount_changed(self):
        for each in self:
            each.discount_changed = False
            if each.order_line:
                result = any(line.discount_changed for line in self.order_line)
                each.discount_changed = result

    

    @api.depends('partner_id','team_id')
    def _compute_partner_pricelist_team_id(self):
        for rec in self:
            rec.partner_pricelist_team_id = rec.sudo().partner_pricelist_ids.filtered(lambda r:r.team_id.id == rec.team_id.id)
            rec.payment_term_id = self.partner_pricelist_team_id.payment_term_id.id
            rec.pricelist_id = self.partner_pricelist_team_id.pricelist_id.id
            # perubahan ORM -> Query untuk mencari partner pricelist team
            # self.env.cr.execute(""" SELECT id,payment_term_id,pricelist_id FROM "partner_pricelist" WHERE id in %s AND team_id=%s""",(tuple(self.partner_pricelist_ids.ids) if self.partner_pricelist_ids else tuple(str(0)),rec.team_id.id or 0))
            # sql  = self.env.cr.fetchall()
            # print("_compute_partner_pricelist_team_id_sql",[x[0] for x in sql])
            # rec.partner_pricelist_team_id = sum([x[0] for x in sql])

    @api.onchange('partner_id','partner_shipping_id')
    def _onchange_sale_mix_ids(self):
        partner_id = self.partner_id.id or 0
        partner_shipping_id = self.partner_shipping_id.id or 0
        query = """
            SELECT so.id FROM sale_order so
            LEFT JOIN stock_picking sp ON sp.sale_id = so.id
            WHERE (sp.state in ('draft','waiting','confirmed') or sp.id is null)
            AND so.partner_id = %s AND so.partner_shipping_id = %s
        """
        self.env.cr.execute(query, (partner_id,partner_shipping_id))
        res = self.env.cr.fetchall()

        ids = [row[0] for row in res]
        if len(ids):
            domain = [('id','in',ids)]
            return {'domain':{'sale_mix_ids':domain}}
        else:
            return {'domain':{'sale_mix_ids':[('id','=',False)]}}

    @api.onchange('user_id')
    def onchange_user_id(self):
        pass

    @api.onchange('team_id')
    def _onchange_team_id(self):
        if self.team_id:
            res = {'domain':{'partner_id':[('is_company','=',True),('state','=','approved'),('id','in',self.team_id.allowed_partner_ids.ids)]}}
            return res
        else:
            return {'domain':{'partner_id':[('is_company','=',True),('state','=','approved')]}}

    def __authorized_form(self, root):
        def append_nocreate_options(elm):
            
            fields_name = elm.attrib.get('name')

            Many2one = isinstance(self._fields[fields_name], fields.Many2one)
            Many2many = isinstance(self._fields[fields_name], fields.Many2many)
            # One2many = isinstance(self._fields[fields_name], fields.One2many)
            if elm.tag!='field':
                return elm
            
            fields_name = elm.attrib.get('name')

            Many2one = isinstance(self._fields[fields_name], fields.Many2one)
            Many2many = isinstance(self._fields[fields_name], fields.Many2many)
            if elm.tag!='field':
                return elm
            options = elm.get('options')
            if options:
                if (Many2one or Many2many):
                    # IF HAS EXISTING "attrs" ATTRIBUTE
                    options_dict = literal_eval(options)
                    options_nocreate = options_dict.get('no_create')
                
                    # if had existing readonly rules on attrs will append it with or operator
                    options_dict.update({"no_create":1})
            else:
                if (Many2one or Many2many):
                    options_dict = {"no_create":1}
                    
            try:
                new_options_str = str(options_dict)
                elm.set('options',new_options_str)
                
            except Exception as e:
                pass
            return elm  
        def set_nocreate_on_fields(elms):
            for elm in elms:
                if elm.tag=='field':
                    elm = append_nocreate_options(elm)
                else:
                    if len(elm)>0:
                        _logger.info((len(elm)))
                        # if elm.tag in ['tree','kanban','form','calendar']:
                        #   continue # skip if *2many field child element
                        elm = set_nocreate_on_fields(elm)
                    else:
                        if elm.tag=='field':
                            elm = append_nocreate_options(elm)
            return elms
        
        def append_readonly_limit_approval(elm):
            if elm.tag!='field':
                return elm

            attrs = elm.get('attrs')
            if attrs:
                # IF HAS EXISTING "attrs" ATTRIBUTE
                attrs_dict = literal_eval(attrs)
                attrs_readonly = attrs_dict.get('readonly')
                # if had existing readonly rules on attrs will append it with or operator
                if attrs_readonly:
                    if type(attrs_readonly) == list:
                        # readonly if limit_approval_state not in draft,approved
                        # incase:
                        # when so.state locked (if limit automatically approved the limit_approval_state will still in draft) so will use original functions
                        # when so.state == draft and limit approval strate in (need_approval_request,  need_approval, reject) will lock the field form to readonly
                        attrs_readonly.insert(0,('state','not in',['draft']))
                        attrs_readonly.insert(0,'|')
                    attrs_dict.update({'readonly':attrs_readonly})
                else:
                    # if not exsit append new readonly key on attrs
                    attrs_dict.update({'readonly':[('state','not in',['draft'])]})
            else:
                attrs_dict = {'readonly':[('state','not in',['draft'])]}
            try:
                new_attrs_str = str(attrs_dict)
                elm.set('attrs',new_attrs_str)
            except Exception as e:
                pass

            return elm


        def set_readonly_on_fields(elms):
            for elm in elms:
                if len(elm)>0:
                    _logger.info("has %s child(s)" % (len(elm)))
                    if elm.tag in ['tree','kanban','form','calendar']:
                        continue # skip if *2many field child element
                    elm = set_readonly_on_fields(elm)
                else:
                    if elm.tag=='field':
                        # elm = append_readonly_limit_approval(elm)
                        
                        # elm.set('readonly','True')
                        elm = append_readonly_limit_approval(elm)
            return elms

        
        # form = root.find('form')
        paths = []
        for child in root:
            
            if child.tag=='sheet':
                # child = append_readonly_limit_approval(child)
                
                child = set_readonly_on_fields(child)
                child = set_nocreate_on_fields(child)
        return root

    @api.model
    def _fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        sup = super()._fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)

        # if form
        if view_type=='form':
            root_elm = ET.fromstring("%s" % (sup['arch']), parser=ET.XMLParser(encoding='utf-8'))
            # AUTHORIZED ALL "<field>" element
            new_view = self.__authorized_form(root_elm)
            sup.update({'arch':ET.tostring(new_view)})

        return sup

    # @api.onchange('validity_date')
    # def _onchange_validity_date(self):
    #     today = fields.Date.today()
    #     if self.validity_date != False:
    #         if self.validity_date < today:
    #             raise UserError (_('Date must be higher than today!'))


    def _compute_origin_interco_order_id(self):
        self = self.with_user(SUPERUSER_ID)
        for rec in self:

            res = self.env['sale.order']
            if rec.auto_generated:
                res = rec.auto_purchase_order_id.interco_sale_id.id

            rec.origin_interco_order_id = res


    # @api.depends('partner_id')
    # def _compute_overdue_invoice_ids(self):
    #     fetch_ids = []
    #     if self.ids:
    #         query = "SELECT id FROM account_move WHERE partner_id in %s AND state in ('posted') AND invoice_date_due <= NOW() and company_id = %s"
    #         partner = self.mapped('partner_id')
    #         self.env.cr.execute(query, (tuple(partner.ids), self.env.company.id))
    #         fetch_ids = list(map(lambda r:r[0], self.env.cr.fetchall()))
            

    #     if len(fetch_ids):
    #         invoices = self.env['account.move'].with_user(1).browse(fetch_ids)
    #         for rec in self:
    #             rec.overdue_invoice_ids = invoices.filtered(lambda r:r.partner_id.id==rec.partner_id.id)
    #     else:
    #         for rec in self:
    #             rec.overdue_invoice_ids = self.env['account.move']

    # Update 22 june 2022 Andri(Proses ketika sebelum edit sudah tidak lama, tapi stelah edit masih lama dikarenakan overdue)
    # @api.depends('partner_id')
    def _compute_overdue_invoice_ids(self):
        # for rec in self:
        #     if rec.plant_id:
        #         query = """SELECT id FROM account_move WHERE partner_id="""+str(int(self.partner_id.id))+""" AND state in ('posted') AND invoice_date_due <= NOW() and company_id ="""+str(int(self.env.company.id))+"""
        #         AND amount_residual_signed > 0"""
        #         # partner = self.mapped('partner_id')
        #         # print("self.mapped('partner_id')",self.mapped('partner_id'))
        #         cr= self.env.cr
        #         cr.execute(query,())
        #         result= cr.fetchall()
        #         fetch_ids = [x[0] for x in result]
        #         print("fetch_ids",len(fetch_ids))
        #         print("fetch_ids",fetch_ids)
        #         rec.overdue_invoice_ids = fetch_ids
        #     else:
        #         rec.overdue_invoice_ids = rec.overdue_invoice_ids
        # perubahan perhitungan overdue
        if self.ids:
            print("IDSS =============", self.ids)
            query = """SELECT id FROM account_move WHERE partner_id="""+str(int(self.partner_id.id))+""" AND state in ('posted') AND invoice_date_due <= NOW() and company_id ="""+str(int(self.env.company.id))+"""
            AND amount_residual_signed > 0"""

            cr= self.env.cr
            cr.execute(query,())
            result= cr.fetchall()
            fetch_ids = [x[0] for x in result]
            if len(fetch_ids):
                self.overdue_invoice_ids = fetch_ids
            else:
                self.overdue_invoice_ids = self.env['account.move']
        else:
            self.overdue_invoice_ids = self.overdue_invoice_ids
    

    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.company_id.id:
            self.interco_master = self.company_id.using_interco_master_on_sale
        else:
            self.interco_master = False

    def credit_validation(self):
        self.ensure_one()
        res = True
        if int(self.status_so) != 0:
            # if limit_approval_state draft
            # is new
            if self.limit_approval_state in ['draft']:
                self.limit_approval_state = 'need_approval_request'
                self.btn_request_approval_limit()
                res = False
            elif self.limit_approval_state not in ['approved']:
                res = True
        return res


    def _validating_confirming_state(self):
        alloweds_state = ['draft']
        alloweds_limit = ['draft','approved']
        
        for rec in self:
            if rec.state in alloweds_state:
                if rec.limit_approval_state not in alloweds_limit:
                    # dict(found._fields['day_index'].selection).get(found.day_index),
                    raise ValidationError(_("Cant Confirming Order! Please Check Limit Approval State! Current Limit State: %s") % (dict(rec._fields['limit_approval_state'].selection).get(rec.limit_approval_state)))

            # must at least 1 item
            
            if len(rec.order_line)<1:
                self.env.cr.rollback()
                return {
                    'effect': {
                        'fadeout': 'slow',
                        'message': _("No item(s) to order was defined. At least require to defined 1 item to order!"),
                        'img_url': '/sanqua_sale_flow/static/src/img/wow.png',
                        'type': 'rainbow_man',
                    }
                }

    def action_draft(self):
        super().action_draft()
        self.limit_approval_state = 'draft'
        self.reset_approvers()

    def unreserve_for_interco(self):
        self = self.filtered(lambda r:r.interco_master)
        if len(self) and len(self.mapped('picking_ids')):
            # unreserve only when picking "Ready"
            pickings = self.mapped('picking_ids').filtered(lambda r:r.state=='assigned')
            pickings.do_unreserve()


    """ Override action_confirm
    
    """ 
    def action_confirm(self):
        self.ensure_one()
        if self.currency_id.id == False:
            self.currency_id = self.company_id.currency_id.id
        
        if self.pricelist_id.id==False and len(self.partner_id.ref_company_ids) and self._context.get('plant_confirm'):
            # pricelists = self.env['product.pricelist'].search([('company_id','=',False)]).filtered(lambda r:'Intercompany Pricelist' in r.name)
            pricelists = self.env['inter.company.pricelist'].get_intercompany_pricelist(company=self.company_id,partner=self.partner_id)
            if len(pricelists)>1:
                pricelists = pricelists[0]
            
            self.pricelist_id = pricelists.pricelist_id.id

        if self._context.get('ORIGINAL_CONFIRM'):
            self.limit_approval_state = 'approved'
            return super().action_confirm()
        
        def check_non_agreement_approval():

            if not self.sale_agreement_id.id and not self._context.get('force_approval',False):
                self.checking_approval_matrix(delete_current=False,tag='so.non.agreement')
        
        self._check_agreement_qty()
        self.check_blacklist()
        checking = self._validating_confirming_state()
        
        if type(checking)==dict:
            return checking
        
        no_return = False

        self._set_status_so()
        if not self.auto_generated:
            if not self.credit_validation():
                no_return = True
        
        if not no_return:
            env = self #default env / origin
            if self.auto_generated:
                # if so generated by intercompany process will change environtment company
                env = self.with_user(1).with_context(force_company=self.company_id.id)
                sup = super(SaleOrder, env).action_confirm()
            else:

                # on self.credit_validation() will call checking_approval_matrix() wich require any approvers list if credit status != 0
                # but if credit status ==0 will return without any approvers list
                # so we need to check again checking_approval_matrix(require_approver=False) --> no require approver
                if self.limit_approval_state!='approved':
                    check_non_agreement_approval()
                
                if self.interco_master:
                    # sup = self.with_context(dict(limit_approved=True)).action_confirm()
                    # sup = super(SaleOrder, self.with_context(limit_approved=True)).action_confirm()
                    sup = super(SaleOrder, self.with_context({'force_validating_interco_lot':True})).action_confirm()
                else:
                    sup = super(SaleOrder, env).action_confirm()
            self.unreserve_for_interco()
            return sup
        else:
            if self.approved:
                return super(SaleOrder, self).action_confirm()
            check_non_agreement_approval()

    @api.onchange('order_pickup_method_id')
    def onchange_pickup_method(self):
        self = self.sudo()
        res = {}
        team_id = self.team_id
        if self.sale_agreement_id.id:
            team_id = self.sale_agreement_id.team_id.id

        values = {
                    'partner_can_direct_pickup':False,
                }

        if self.order_pickup_method_id.id and self.partner_id.id:
            if self.order_pickup_method_id.id == self.env.ref('sanqua_sale_flow.order_pickup_method_take_in_plan').id:
                updated = {
                    'partner_can_direct_pickup':self.partner_id.can_direct_pickup,
                }
                values.update(updated)
            else:
                values.update({
                    'partner_can_direct_pickup':self.partner_id.can_direct_pickup,
                    })
        else:
            if self.partner_id.id==False:
                values.update({'order_pickup_method_id':False})
                if self.order_pickup_method_id.id:
                    res.update({'warning':{'title':_("Attention!"),'message':_("Please Select Customer First!")}})


        if self.order_line:
            for line in self.order_line:
                line.product_id_change()
                line.product_uom_change()
        
        self.update(values)



        res.update({'value':values})
        return res




    # @api.depends('partner_id','amount_total')
    def _set_status_so(self):
        # super(SaleOrder, self)._set_status_so()
        for rec in self:
            rec.status_so = rec.status_so
            pricelist = rec.partner_id.sudo().partner_pricelist_ids.filtered(lambda r:r.sudo().team_id.id==rec.sudo().team_id.id).sorted('id', reverse=True)
            
            if len(pricelist)>0:
                pricelist = pricelist[0].sudo()
                status_so = '0'
                if pricelist.black_list == 'blacklist':
                    status_so = '4'
                # penambahan function untuk notif ovdue,over limit dan overdue & over limit
                # elif pricelist.over_due == 'overdue':
                #     status_so = '1'
                # elif pricelist.remaining_limit < rec.amount_total:
                #     status_so = '2'
                # elif pricelist.over_due == 'overdue' and pricelist.remaining_limit < rec.amount_total:
                #     status_so = '3'
                elif pricelist.over_due == 'overdue' and pricelist.remaining_limit >= rec.amount_total:
                    status_so = '1'
                elif pricelist.over_due != 'overdue' and pricelist.remaining_limit < rec.amount_total:
                    status_so = '2'
                elif pricelist.over_due == 'overdue' and pricelist.remaining_limit < rec.amount_total:
                    status_so = '3'

                rec.update({
                    'status_so':status_so,
                    })

    def btn_cancel_approval(self):
        self.ensure_one()
        if self.state not in ['sale']:
            raise ValidationError(_("Only can cancel when Order Confirmation!"))
        if self.env.user.id not in self.approvers_user_ids.ids:
            raise AccessError(_("You don't have authorization for canceling this document!\nOnly Approvers can canceling document!"))
        self.action_cancel()


    def btn_request_approval_limit(self):
        if not self._context.get('force_approval'):
            self.checking_approval_matrix()
            self.filtered(lambda r:r.limit_approval_state=='need_approval_request').write(dict(limit_approval_state = 'need_approval'))


    def btn_approve_limit(self):
        # OLD ONE
        # if self.user_has_groups('!sanqua_sale_flow.group_credit_limit_approver'): 
        #   raise AccessError(_("You're not authorized to approving the document(s)!"))
        # NEW ONE
        # NEW ONE USING approval_matrix module
        self.check_blacklist()
        self.approving_matrix()
        if self.approved:
            self.filtered(lambda r:r.limit_approval_state=='need_approval').write(dict(limit_approval_state = 'approved'))
            self.with_context(dict(limit_approved=True)).action_confirm()

    def open_reject_message_wizard(self):
        self.ensure_one()
        
        form = self.env.ref('approval_matrix.message_post_wizard_form_view')
        context = dict(self.env.context or {})
        context.update({'default_prefix_message':"<h4>Rejecting Sales Order</h4>","default_suffix_action": "btn_reject_limit"}) #uncomment if need append context
        context.update({
            'active_model':'sale.order',
            'active_id':self.id,
            'active_ids':self.ids,
        })
        res = {
            'name': "%s - %s" % (_('Rejecting Sale'), self.name),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'message.post.wizard',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res

    def btn_reject_limit(self):
        # self.ensure_one()
        # OLD ONE
        # if self.user_has_groups('!sanqua_sale_flow.group_credit_limit_approver'):
        #   raise AccessError(_("You're not authorized to rejecting the document(s)!"))
        # END
        # NEW ONE USING approval_matrix module
        
        self.rejecting_matrix()
        # END
        to_reject = self.filtered(lambda r:r.limit_approval_state=='need_approval')
        to_reject.write(dict(limit_approval_state='rejected'))
        to_reject.action_cancel()


    """Create copy of origin stock.interco.move.line
    @self = so plant to Origin Company

    Method to copy original so from original interco procurement so (do to customer). Find it and copy it into DO from plant to Request Company
    """
    def _copy_selected_interco_move_line(self):
        if self.state=='draft':
            raise ValidationError(_("You should checklist automatic validation for intercompany confirmation picking %s/%s") % (self.env.company.display_name,self.sudo().company_id.display_name))
        self.ensure_one()
        self = self.with_user(SUPERUSER_ID).with_context(force_company=self.company_id.id,allowed_company_ids=self.company_id.ids+self.company_id.ids)

        self.picking_ids.filtered(lambda r:r.state=='assigned').do_unreserve()


        IntercoMoveLine = self.env['stock.interco.move.line']
        MoveLine = self.env['stock.move.line']
        skip_moves = self.env['stock.move']
        for picking in self.origin_interco_order_id.picking_ids.filtered(lambda r:r.picking_type_id.code=='outgoing' and r.state not in ['draft','cancel','done']):
            # picking = picking on source (WIM)
            # self = self order in plant
            movesstatus = {}
            for move in picking.move_lines.sorted('product_uom_qty', reverse=True):
                # move = move in picking (WIM)

                # origin_interco_move_lines = picking.interco_move_line_ids.filtered(lambda r: \
                #     r.product_id.id==move.product_id.id \
                #     and r.move_id.id == move.id)

                origin_interco_move_lines = move.interco_move_line_ids
                if len(origin_interco_move_lines):
                    for origin_interco_move_line in origin_interco_move_lines:
                        new_data = {}
                        # interco_data = origin_interco_move_line._convert_to_write({name: getattr(origin_interco_move_line, name) for name in origin_interco_move_line._fields})
                        # interco_move = stock.move() -> with company "Plant"

                        interco_move = self.picking_ids.filtered(lambda r:r.picking_type_id.code=='outgoing') \
                            .mapped('move_lines') \
                            .filtered(lambda r:r.product_id.id==move.product_id.id and r.id not in skip_moves.ids and r.sale_line_id.product_uom_qty>=origin_interco_move_line.qty).sorted('product_uom_qty', reverse=False) # find same move on interco move from origin interco move
                        if len(interco_move)>1:
                            # find move with product_uom_qty == WIM->product_uom_qty(matched)
                            new_interco_move = interco_move.filtered(lambda r:r.product_uom_qty==move.interco_move_line_qty_done)
                            if len(new_interco_move)>1:
                                # ordered = interco_move.sorted('qty')
                                interco_move = new_interco_move[0]
                                
                            elif len(new_interco_move)==0:
                                interco_move = interco_move.filtered(lambda r:r.product_uom_qty<=move.product_uom_qty)[0]
                            elif len(new_interco_move)==1:
                                interco_move = new_interco_move
                        exist_move = movesstatus.get(str(interco_move.id))
                        if not len(interco_move):
                            raise ValidationError(_("No Interco Move Reference Found:Err 2001"))

                        if exist_move:
                            after_qty = float(exist_move)+origin_interco_move_line.qty
                            movesstatus.update({str(interco_move.id):after_qty})
                            if after_qty >= interco_move.sale_line_id.product_uom_qty:
                                skip_moves += interco_move
                        else:
                            # if not registered
                            after_qty = origin_interco_move_line.qty
                            movesstatus.update({str(interco_move.id):after_qty})
                            if after_qty >= interco_move.sale_line_id.product_uom_qty:
                                skip_moves += interco_move

                        new_data.update(dict(
                            product_id=interco_move.product_id.id, 
                            product_uom_id=interco_move.product_id.uom_id.id,
                            picking_id=interco_move.picking_id.id, 
                            move_id=interco_move.id, 
                            lot_id=origin_interco_move_line.lot_id.id, 
                            qty_done=origin_interco_move_line.qty,
                            # merubah default location ketika create account move line
                            location_id=interco_move.location_id.id,
                            # location_id=origin_interco_move_line.src_location_id.id,
                            location_dest_id=interco_move.location_dest_id.id,
                            company_id=self.company_id.id))
                        
                        
                        
                        mvl = MoveLine.new(new_data)
                        mvl.onchange_product_id()
                        
                        new_mvl = mvl._convert_to_write({name:mvl[name] for name in mvl._cache})
                        created_obj = MoveLine.create(new_data)

    def recompute_coupon_lines(self,confirm_all=False):
        if self._context.get('no_reward'):
            return
        for order in self:
            print('>>> Order : ' + str(order))
            order._remove_invalid_reward_lines()
            programs = order._create_new_no_code_promo_reward_lines()
            order._update_existing_reward_lines()
            if programs:
                if confirm_all:
                    wizard_id = self.env['sale.coupon.applied.wizard'].with_context(dict(line_ids=programs.ids)).create({
                        'sale_id':order.id
                    })
                    wizard_id.btn_confirm()
                else:
                    form = self.env.ref('sanqua_sale_flow.sale_coupon_applied_wizard_view_form')
                    res = {
                        'name': "%s - %s" % (_('Applied Program Promotions'), self.name),
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'sale.coupon.applied.wizard',
                        'view_id': form.id,
                        'type': 'ir.actions.act_window',
                        'context':{'default_sale_id':order.id,'line_ids':programs.ids},
                        'target': 'new'
                    }
                    return res
            else:
                return

    def _create_new_no_code_promo_reward_lines(self):
        '''Apply new programs that are applicable'''
        self.ensure_one()
        order = self
        programs = order._get_applicable_no_code_promo_program()
        programs = programs.filtered(lambda r: r.state == 'done')
        if len(programs) >= 1 :
            return programs
        else:
            return super(SaleOrder, self)._create_new_no_code_promo_reward_lines()

    def _get_sales_can_be_cancel(self):
        # multi possible
        sale_ids = self.env['sale.order']
        sales = self.filtered(lambda r:r.state not in ['cancel'])

        if len(sales):
            # check picking
            for sale in sales:
                if all(sale.picking_ids.mapped(lambda r:r.state not in ['done','plant-confirmed','assigned'])):
                    sale_ids += sale
        
        return sale_ids

    def action_locked(self):
        self.ensure_one()
        orders = self.filtered(lambda s: s.state in ['draft', 'confirm'])
        return orders.write({'state': 'locked'})

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    qty_stock = fields.Float(compute="_get_stock", store=True, string="Avail. Stock")

    limit_approval_state = fields.Selection(related="order_id.limit_approval_state", readonly=True)

    take_in_plant_disc_nom = fields.Monetary(string="Take In Plant Disc", compute="_compute_agreement", store=True)

    discount_changed = fields.Boolean(compute='_compute_discount_changed')

    allowed_company_ids = fields.Many2many('res.company', related="order_id.allowed_company_ids")

    price_subtotal_include = fields.Float(compute='_compute_price_subtotal_include', string='Subtotal Include')
    
    @api.depends('price_subtotal','price_tax')
    def _compute_price_subtotal_include(self):
        for rec in self:
            rec.price_subtotal_include = rec.price_subtotal + rec.price_tax

    def product_not_allowed(self):
        if self.order_id.partner_id and (self.order_id.partner_id.ref_company_ids.ids)==0 and self.product_id:
            if self.product_id.categ_id.id not in self.order_id.partner_id.allowed_product_category_ids.ids:
                allowed = []
                for categ in self.order_id.partner_id.allowed_product_category_ids:
                    allowed.append(categ.name)
                raise UserError(_('Sorry Customer %s cant buy product %s. Only allowed to buy in ( %s ).') % (self.order_id.partner_id.name,self.product_id.display_name,', '.join(allowed)))

    @api.onchange('product_id')
    def _onchange_product_not_allowed(self):
        self.product_not_allowed()
        
    @api.constrains('product_id')
    def _constrains_product_not_allowed(self):
        self.product_not_allowed()

    @api.depends('discount_fixed_line')
    def _compute_discount_changed(self):
        for each in self:
            each.discount_changed = False
            if each.order_id.order_pickup_method_id.price_unit_discount_agreement==True:
                agreement_line_id = each.agreement_line_id or False
                if agreement_line_id:
                    if agreement_line_id.discount != each.discount:
                        each.discount_changed = True
                    else:
                        each.discount_changed = False

    @api.constrains('discount')
    def constrains_discount(self):
        for rec in self:
            # if rec.discount_changed:
            #     raise UserError(_("Cant change discount out of agreement!"))
            print('AA')
    
    @api.constrains('price_unit')
    def _constrains_price_unit(self):
        for each in self:
            if each.agreement_line_id.id and each.agreement_line_id.price_unit != each.price_unit:
                raise UserError (_('Price unit set to %s not equal with wich defined at sale agreement %s (%s)!') % (each.price_unit, each.agreement_line_id.agreement_id.name, each.agreement_line_id.price_unit,))

    @api.depends('order_id.sale_agreement_id','product_id')
    def _compute_agreement(self):
        for rec in self:
            values = {
                'take_in_plant_disc_nom':0.0
            }
            if rec.order_id and rec.order_id.sale_agreement_id.id:
                # find same product
                agreement_line = rec.order_id.sale_agreement_id.agreement_line_ids.filtered(lambda r:r.product_id.id == rec.product_id.id)
                _logger.info(agreement_line)
                if len(agreement_line):
                    if len(agreement_line)>1:
                        agreement_line = agreement_line[0]
                    # if discount 
                    if rec.order_id.order_pickup_method_id.price_unit_discount_agreement:    
                        # values.update({'take_in_plant_disc_nom': ((agreement_line.discount/100) * agreement_line.price_unit) if agreement_line.discount>0.0 else 0.0})
                        values.update({'take_in_plant_disc_nom':agreement_line.disc_amount})
                    
            rec.update(values)


    @api.depends('product_id','order_id.warehouse_id','order_id.state')
    def _get_stock(self):
        self = self.with_user(SUPERUSER_ID)
        for line in self:
            if line.order_id.interco_master:
                location = line.order_id.plant_id.warehouse_id.lot_stock_id
                company = line.order_id.plant_id
            else:
                location = line.order_id.warehouse_id.lot_stock_id
                company = line.company_id
            avaliable_qty = 0
            available_qty = line.with_context(dict(force_company=company.id, location_id=location.id)).product_id.free_qty
            line.qty_stock = available_qty

    
    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        res = super(SaleOrderLine, self).product_uom_change()

        if self.order_id.sale_agreement_id:
            aggreement_price = self._check_price_product(self.product_id, self.order_id.sale_agreement_id)
            
            if len(aggreement_price):
                
                if self.order_id.order_pickup_method_id.price_unit_discount_agreement==True:
                    # price_unit = float(aggreement_price.price_unit - (aggreement_price.price_unit * (aggreement_price.discount / 100.0)))
                    price_unit = aggreement_price.price_unit
                    self.price_unit = price_unit
                    
                    self.discount_fixed_line = aggreement_price.disc_amount
                else:
                    price_unit = aggreement_price.price_unit
                    self.price_unit = price_unit
                    self.discount_fixed_line = 0.0
                
                
        return res

    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'order_id.state')
    def _get_to_invoice_qty(self):
        """
        Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
        calculated from the ordered quantity. Otherwise, the quantity delivered is used.
        """

        for line in self.filtered(lambda r:r.order_id.auto_generated==True):
            if line.order_id.state in ['sale', 'done']:
                line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

        non_auto_generated = self.filtered(lambda r:r.order_id.auto_generated==False)
        if len(non_auto_generated):
            super(SaleOrderLine, non_auto_generated)._get_to_invoice_qty()

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id','discount_fixed_line')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit - line.discount_fixed_line
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })