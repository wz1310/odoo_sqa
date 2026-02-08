# -*- encoding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError
import xml.etree as etr
import xml.etree.ElementTree as ET
from ast import literal_eval
import logging
_logger = logging.getLogger(__name__)


class SaleOrderPromotion(models.Model):
    _name = "sale.order.promotion"
    _inherit = ['mail.thread', 'mail.activity.mixin'] + ["approval.matrix.mixin"]
    # _inherits = {'sale.order': 'sale_id'}
    _description = "Form Support Promotion"

    def unlink(self):
        if self.state not in ['canceled']:
            raise UserError(_("Cancel only allowed when canceled!"))

    @api.model
    def _default_validity_date(self):
        if self.env['ir.config_parameter'].sudo().get_param('sale.use_quotation_validity_days'):
            days = self.env.company.quotation_validity_days
            if days > 0:
                return fields.Date.to_string(datetime.now() + timedelta(days))
        return False

    sale_id = fields.Many2one(comodel_name='sale.order', string='Sale Order',ondelete='cascade',auto_join=True, index=True, readonly=True)
    # promotion_desc_id = fields.Many2one(comodel_name='sale.order.promotion.description', string='Document Description', required=True)
    name = fields.Char(string='Name', required=True, copy=False, readonly=False, states={}, index=True, default='New')
    user_id = fields.Many2one('res.users', string="Salesperson", default=lambda self: self.env.user, readonly=False, states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string="Company", 
        required=True, default=lambda self: self.env.company.id,
        readonly=True, states={'draft': [('readonly', False)]})
    division_id = fields.Many2one('crm.team', string="Division", required=True, default=False, domain=False, readonly=False, states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one(
        'res.partner', string='Customer', required=True, readonly=False, states={'draft': [('readonly', False)]})

    ##dion##
    spesific_partner_id = fields.Many2one(
        'res.partner', string='Spesific Customer', required=True, readonly=False,domain=[('customer','=',True)], states={'draft': [('readonly', False)]})

    partner_shipping_id = fields.Many2one(
        'res.partner', string='Delivery Address', required=True, 
        readonly=False, states={'draft': [('readonly', False)]})
    validity_date = fields.Date(
        string='Expiration',default=_default_validity_date, readonly=False, 
        states={'draft': [('readonly', False)]})
    date_order = fields.Datetime(
        string='Document Date', required=True, readonly=False, index=True,
        copy=False, default=fields.Datetime.now,)
    internal_memo = fields.Text(string='Memo', 
        readonly=False, states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('needapproval', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('canceled', 'Canceled'),
        ], string='Status', readonly=False, copy=False, index=True, default='draft')
    promotion_desc = fields.Selection([
        ('product_event', 'Request Sample Product For Event'),
        ('product_sample', 'Request Sample Product For Lead Customers'),
        ], string='Document Description', required=True,
        readonly=False, states={'draft': [('readonly', False)]})
    order_line = fields.One2many(
        'sale.order.promotion.line', 'order_id', string='Order Lines',
        copy=True, auto_join=True, readonly=True, states={'draft': [('readonly', False)]})
    picking_ids = fields.One2many('stock.picking', 'sale_promotion_id', string='Promo Transfers')
    delivery_count = fields.Integer(string='Delivery Orders', compute='_compute_picking_ids')
    pricelist_id = fields.Many2one(
        'product.pricelist', string='Pricelist', required=True,
        readonly=True, states={'draft': [('readonly', False)]})


    def __authorized_form(self, root):
        def append_nocreate_options(elm):
            # _logger.info(('---- loop', elm.tag,elm.attrib.get('name')))
            
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
                        # 	continue # skip if *2many field child element
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

    @api.depends('picking_ids')
    def _compute_picking_ids(self):
        for order in self:
            order.delivery_count = len(order.with_user(1).sale_id.picking_ids)

    @api.onchange('division_id')
    def onchange_division_id(self):
        res = {
            'domain':{
                'user_id':False
            }
        }
        if self.division_id.id:
            res['domain'].update({'user_id':[('id','in',self.division_id.sales_user_ids.ids)]})
            if self.user_id.id:
                # if user_id filled
                # check if on division.sales_user_ids
                if self.user_id.id not in self.division_id.sales_user_ids.ids:
                    self.user_id = False
        
        return res

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Delivery address
        """
        if not self.partner_id:
            self.update({
                'pricelist_id': False,
                'partner_shipping_id': False,
            })
            return

        addr = self.partner_id.address_get(['delivery'])
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'partner_shipping_id': addr['delivery'],
        }
        self.update(values)

    def action_view_delivery(self):
        '''
        This function returns an action that display existing delivery orders
        of given sales order ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''
        action = self.env.ref('stock.action_picking_tree_all').read()[0]

        pickings = self.sale_id.mapped('picking_ids')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = pickings.id
        # Prepare the context.
        picking_id = pickings.filtered(lambda l: l.picking_type_id.code == 'outgoing')
        if picking_id:
            picking_id = picking_id[0]
        else:
            picking_id = pickings[0]
        action['context'] = dict(self._context, default_partner_id=self.partner_id.id, default_picking_id=picking_id.id, default_picking_type_id=picking_id.picking_type_id.id, default_origin=self.name, default_group_id=picking_id.group_id.id)
        return action

    def btn_submit(self):
        if len(self.order_line)==0:
            raise UserError(_('At least 1 item to order required!'))
        self.checking_approval_matrix(add_approver_as_follower=True)
        self.state = 'needapproval'

    def action_approve(self):
        if self.approved:
            self.sale_id.action_confirm()
            self.state = 'approved'

    def btn_approve(self):
        # self.state = 'approved'
        # self.sale_id.action_confirm()
        self.approving_matrix(post_action='action_approve')

    def btn_draft(self):
        self.state = 'draft'

    def btn_reject(self):
        self.state = 'rejected'
        self.rejecting_matrix()

    @api.model
    def create(self, vals):
        if vals.get('name','New') == 'New':
            vals['name'] = self.env['ir.sequence'].sudo().next_by_code('sale.order.promotion')

        result = super(SaleOrderPromotion, self).create(vals)
        sale_order_obj = self.env['sale.order']
        sale_order_line_obj = self.env['sale.order.line']
        so_obj = {
			'partner_id': result.partner_id.id,
			'partner_invoice_id': result.partner_id.id,
			'partner_shipping_id': result.partner_shipping_id.id,
			'pricelist_id': result.pricelist_id.id,
            'is_promotion': 1,
            'company_id': result.user_id.company_id.id,
            'currency_id': result.pricelist_id.currency_id.id,
            'picking_policy': 'direct',
            'order_promotion_id': result.id,
		}
        new_sorder = sale_order_obj.create(so_obj)
        
        for line in result.order_line:
            soline_obj = {
                'order_id':new_sorder.id,
                'product_id':line.product_id.id,
                'product_uom':line.product_uom.id,
                'product_uom_qty':line.product_uom_qty,
                'promotion_line_id':line.id,
                'price_unit':0.00
            }
            sale_order_line_obj.create(soline_obj)
        result.with_context(no_sync=True).update({'sale_id':new_sorder.id})
        return result

    
    def write(self,vals):
        result = super(SaleOrderPromotion, self).write(vals)
        if not self._context.get('no_sync'):
            for rec in self:
                sale_order_obj = self.env['sale.order']
                sale_order_line_obj = self.env['sale.order.line']
                if rec.state == 'draft':
                    sale_order_rec = sale_order_obj.search([
                        ('id','=',rec.sale_id.id)])
                    so_dict={
                        'partner_id': rec.partner_id.id,
                        'partner_invoice_id': rec.partner_id.id,
                        'partner_shipping_id': rec.partner_shipping_id.id,
                        'pricelist_id': rec.pricelist_id.id,
                        'is_promotion': True,
                        'company_id': rec.user_id.company_id.id,
                        'currency_id': rec.pricelist_id.currency_id.id,
                        'picking_policy': 'direct',
                        'order_promotion_id': rec.id
                    }
                    edit_sorder = sale_order_rec.write(so_dict)
                    for line in rec.order_line:
                        sale_order_line_rec = sale_order_line_obj.search([
                            ('promotion_line_id','=',line.id)])
                        if sale_order_line_rec:
                            soline_dict={
                                'product_id':line.product_id.id,
                                'name':line.product_id.name,
                                'product_uom':line.product_uom.id,
                                'product_uom_qty':line.product_uom_qty,
                                'price_unit':0.00
                            }
                            edit_soline = sale_order_line_rec.update(soline_dict)
                        else:
                            soline_new = {
                                'order_id':rec.sale_id.id,
                                'product_id':line.product_id.id,
                                'product_uom':line.product_uom.id,
                                'product_uom_qty':line.product_uom_qty,
                                'promotion_line_id':line.id,
                                'price_unit':0.00
                            }
                            sale_order_line_obj.create(soline_new)
                        delete_soline = sale_order_line_obj.search(['&',
                            ('order_id','=',rec.sale_id.id),
                            ('promotion_line_id','=',False)])
                        delete_soline.sudo().unlink()
        return result
