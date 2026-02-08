"""File Sale Agreement"""
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp

from odoo.tools.misc import formatLang, format_date as odoo_format_date, get_lang
import logging
_logger = logging.getLogger(__name__)

import xml.etree as etr
import xml.etree.ElementTree as ET
from ast import literal_eval

class SaleAgreement(models.Model):
    """ new model sale.agreement"""
    _name = 'sale.agreement'
    _description = 'Sale Agreement'

    _inherit = ['mail.thread', 'mail.activity.mixin']

    _order = 'id desc'

    

    @api.model
    def _get_default_team(self):
        return self.env['crm.team']._get_default_team_id()

    partner_id = fields.Many2one('res.partner', string="Customer", required=True, domain=[('is_company','=',True),('customer','=',True),('state','=','approved')])
    partner_code = fields.Char('Customer Code', related="partner_id.code")
    partner_id = fields.Many2one('res.partner', 'Customer')
    name = fields.Char(string='Agreement Reference', required=True, copy=False, default='New', readonly=True, track_visibility="onchange")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm by Sales'),
        ('approve', 'Approved by Manager'),
        ('locked', 'Locked'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], string='Status', readonly=True, copy=False, index=True, default='draft', required=True, track_visibility="onchange")
    user_id = fields.Many2one('res.users', string='Salesperson', index=True, required=True, track_visibility="onchange")
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company,track_visibility="onchange")
    currency_id = fields.Many2one("res.currency", string="Currency", default=lambda self: self.env.user.company_id.currency_id, readonly=True, required=True, track_visibility="onchange")
    target = fields.Monetary(string='Target', digits=dp.get_precision('Product Price'), default=0.0,track_visibility="onchange")
    start_date = fields.Date(required=True,track_visibility="onchange")
    end_date = fields.Date(required=True,track_visibility="onchange")
    agreement_line_ids = fields.One2many('sale.agreement.line', 'agreement_id',string='Agreement Lines', copy=True, auto_join=True)
    # purchase_ids = fields.One2many('purchase.order', 'sale_agreement_id',
    #     string='Purchase Orders', readonly=True, groups="purchase.group_purchase_user")
    order_count = fields.Integer(compute='_compute_orders_number', string='Number of Orders')
    periode_information = fields.Selection([
        ('running', 'Running'),
        ('finished', 'Finished')],
        compute='_compute_periode_information', copy=False)
    sale_order_ids = fields.One2many('sale.order', 'sale_agreement_id',
        string='Sale Orders', readonly=True)
    total_order = fields.Monetary(string='Total Order', readonly=True, store=True,
        digits=dp.get_precision('Product Price'), compute='_compute_total_order')
    total_volume = fields.Integer(compute='_compute_invoice')
    total_weight = fields.Integer(compute='_compute_invoice')
    weight_uom_name = fields.Char(compute='_compute_weight_uom_name')
    team_id = fields.Many2one('crm.team', 'Division',change_default=True, check_company=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    product_category_ids = fields.Many2many('product.category', related="team_id.product_category_ids")
    product_ids = fields.Many2many('product.product', compute='_compute_product_ids', store=True)
    # karna ada dua pricelist_id maka alah satu di matikan
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', compute="_compute_pricelist")

    supervisor_id = fields.Many2one('res.users', related="team_id.user_id", readonly=True)
    # sales_admin_ids = fields.Many2many('res.users', related="team_id.sales_admin_ids", readonly=True)
    sales_admin_id = fields.Many2one('res.users', compute="_compute_pricelist")
    
    selected_product_ids = fields.Many2many('product.product', compute="_compute_selected_product_ids", string="Selected Products")
    
    amount_untaxed = fields.Monetary(compute='_compute_amount_total', string='Untaxed Amount')
    amount_tax = fields.Monetary(compute='_compute_amount_total', string='Tax')
    amount_total = fields.Monetary(compute='_compute_amount_total', string='Total')
    partner_pricelist_id = fields.Many2one('partner.pricelist', compute="_compute_partner_priceist", store=True)
    # compute untuk pricelist_id ini dirobah dari _compute_partner_priceist -> _compute_pricelist
    # pricelist_id = fields.Many2one('product.pricelist', compute="_compute_partner_pricelist", store=True)


    @api.depends('team_id','partner_id')
    def _compute_partner_priceist(self):
        for rec in self:
            partner_pricelist_id = False
            pricelist_id = False
            if rec.partner_id.id:
                matched = rec.partner_id.partner_pricelist_ids.filtered(lambda r:r.team_id.id==rec.team_id.id)
                partner_pricelist_id = matched.id
                pricelist_id = matched.pricelist_id.id

            rec.update({
                'partner_pricelist_id':partner_pricelist_id,
                'pricelist_id':pricelist_id
                })

    total_product_qty = fields.Float('Total Product Quantity', compute='_compute_total')
    total_release_qty = fields.Float('Total Release Quantity', compute='_compute_total')
    total_remaining_qty = fields.Float('Remaining Quantity', compute='_compute_total')

    def _compute_total(self):
        for rec in self:
            rec.total_product_qty = sum(rec.agreement_line_ids.mapped('product_qty'))
            rec.total_release_qty = sum(rec.agreement_line_ids.mapped('product_qty_sale_order'))
            rec.total_remaining_qty = rec.total_product_qty - rec.total_release_qty

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        return super().copy(default={
            'start_date':fields.Date.today(),
            'end_date':fields.Date.today(),
        })
    
    @api.depends('agreement_line_ids','agreement_line_ids.product_qty','agreement_line_ids.price_unit','agreement_line_ids.tax_ids','agreement_line_ids.price_tax')
    def _compute_amount_total(self):
        for rec in self:
            updated = {
                'amount_untaxed':0.0,
                'amount_tax':0.0,
                'amount_total':0.0,
            }
            
            if rec.agreement_line_ids:
                
                amount_untaxed = sum(rec.agreement_line_ids.mapped('price_subtotal'))
                amount_tax = sum(rec.agreement_line_ids.mapped('price_tax'))
                amount_total = amount_untaxed + amount_tax
                updated = {
                    'amount_untaxed':amount_untaxed,
                    'amount_tax':amount_tax,
                    'amount_total':amount_total,
                }
            rec.update(updated)


    def unlink(self):
        not_draft = self.filtered(lambda r:r.state!='draft')
        if len(not_draft):
            raise UserError(_("Couldn't deleting docs %s") % (", ".join(not_draft.mapped('name')), ))
        
        return super(SaleAgreement, self).unlink()

    @api.onchange('team_id')
    def _onchange_team_id(self):
        if self.team_id:
            if self.partner_id.id:
                if self.team_id.id not in self.partner_id.partner_pricelist_ids.mapped('team_id').ids:
                    # self.partner_id = False
                    self.update({
                        'partner_id':False,
                        'sales_admin_id':False,
                        'pricelist_id':False,
                        'region_group_id':False,
                        'user_id':False,
                    })
            return {'domain':{'partner_id':[('state','=','approved'),('is_company','=',True), ('id','in',self.team_id.allowed_partner_ids.ids)]}}
        else:
            return {'domain':{'partner_id':[('state','=','approved'),('is_company','=',True)]}}

    @api.depends('agreement_line_ids','agreement_line_ids.product_id')
    def _compute_selected_product_ids(self):
        for rec in self:
            rec.selected_product_ids = rec.agreement_line_ids.mapped('product_id')
            # penambahan popup ketika pilih produk tapi tidak ada pricelist
            # if not rec.pricelist_id and len(rec.selected_product_ids)>0:
            #     raise UserError(_("No Pricelist Selected!"))
                # ===============================================>

    @api.depends('partner_id','team_id')
    def _compute_pricelist(self):
        for rec in self:
            partner_pricelist = self.env['partner.pricelist'].get_partner_pricelist(partner=rec.partner_id, team=rec.team_id, user=rec.user_id)
            rec.update({
                'pricelist_id':partner_pricelist.pricelist_id,
                'sales_admin_id':partner_pricelist.sales_admin_id
            })

    def _default_team_id(self):
        return self.env.user.sale_team_ids.id
        
    region_group_id = fields.Many2one('region.group',string="Region",compute='_compute_region')

    @api.depends('partner_id')
    def _compute_region(self):
        for each in self:
            each.region_group_id = False
            if each.partner_id:
                each.region_group_id = each.partner_id.region_group_id.id


    @api.depends('agreement_line_ids', 'agreement_line_ids.product_id')
    def _compute_product_ids(self):
        for data in self:
            data.product_ids = [(6, 0, data.agreement_line_ids.mapped('product_id').ids)]

    @api.constrains('team_id', 'user_id', 'state')
    def _check_maximum_qty_so_based_on_product_qty(self):
        """block if user create with same team_id and user_id before state done"""
        for order in self:
            sales_agreement_ids = self.env['sale.agreement'].search([('team_id', '=', order.team_id.id),
                                                                     ('user_id', '=', order.user_id.id),
                                                                     ('state', 'not in', ('draft', 'done'))])
            if len(sales_agreement_ids) > 1:
                # raise ValidationError(_('You still have active Sales Agreement, Please set Done another Agreement before you create again'))
                pass
    
    @api.constrains('start_date','end_date')
    def _constrains_date(self):
        for rec in self:
            res = rec._onchange_date()
            if type(res)==dict and res.get('warning'):
                warn = res.get('warning')
                raise UserError(_(warn.get('message')))

    @api.onchange('start_date', 'end_date')
    def _onchange_date(self):
        warning_mess = {}
        if self.start_date and self.end_date and self.start_date > self.end_date:
            warning_mess = {
                'title': _('Warning!'),
                'message': _('The end date must not be smaller than the start date')
            }
        
        if self.end_date and self.end_date < fields.Date.today():
            warning_mess = {'title':_("Date not valid!"), "message":_("Date Shouldbe not less than today")}
        
        if warning_mess:
            return {'warning': warning_mess}

    @api.onchange('partner_id', 'team_id', 'user_id')
    def onchange_partner_id(self):
        # <update by andri 10 Nov 22 penambahan fungsi hapus line ketika pricelist di robah
        print("ONCHANGE AGGRE JALAN =========================")
        self.agreement_line_ids = False
        # ========================================>
        default_data = {}
        domain = {}
        if self.team_id.id and self.partner_id.id:
            domain.update({'sales_admin_id':[('id','in',self.team_id.sales_admin_ids.ids)]})
            pricelist_partner = self.partner_id.partner_pricelist_ids.filtered(lambda p: p.team_id.id==self.team_id.id)
            

            if pricelist_partner:
                default_data.update({'pricelist_id':pricelist_partner[0].pricelist_id.id, 'user_id':pricelist_partner.user_id.id, 'sales_admin_id':pricelist_partner.sales_admin_id.id})
            else:
                default_data.update({'pricelist_id':False})
        else:
            if self.partner_id.id:
                default_data.update({'pricelist_id':self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False})
            else:
                default_data.update({'pricelist_id':False})
        

        self.update(default_data)

        return {
            'domain':domain
        }


    def _compute_weight_uom_name(self):
        weight_uom_id = self.env['product.template']._get_weight_uom_id_from_ir_config_parameter()
        for product_template in self:
            product_template.weight_uom_name = weight_uom_id.name

    def _compute_invoice(self):
        today = datetime.now().date()
        for this in self:
            if this.start_date and this.end_date and this.partner_id:
                weight_uom_id = self.env['product.template']._get_weight_uom_id_from_ir_config_parameter()
                query = """
                    select COALESCE(c.weight, 0) as weight, b.quantity as quantity, e.id as id, e.name as uom, f.id as category, d.uom_id as uom_product,
                        COALESCE(c.volume, 0) as volume 
                    from account_move a
                    inner join account_move_line b on a.id = b.move_id
                    inner join product_product c on b.product_id = c.id
                    inner join product_template d on d.id = c.product_tmpl_id
                    inner join uom_uom e on e.id = b.product_uom_id
                    inner join uom_category f on f.id = e.category_id
                    where a.invoice_date >= %s and a.invoice_date <= %s and d.type = 'product' and a.type = 'out_invoice'
                    and a.state not in ('cancel', 'draft') and a.partner_id = %s
                """
                params = (this.start_date, this.end_date, this.partner_id.id,)
                self.env.cr.execute(query, params)
                result = self.env.cr.dictfetchall()
                total_weight = 0
                total_volume = 0
                for data in result:
                    uom_invoice = self.env['uom.uom'].browse(data['id'])
                    uom_product = self.env['uom.uom'].browse(data['uom_product'])
                    if weight_uom_id.category_id == uom_product.category_id:
                        product_qty = uom_invoice._compute_quantity(data['quantity'], uom_product, rounding_method='UP')
                        weight = product_qty * data['weight']
                        total_weight = total_weight + weight
                    elif weight_uom_id.category_id != uom_product.category_id:
                        weight = data['weight'] * data ['quantity']
                        total_weight = total_weight + weight
                    volume = data['volume'] * data['quantity']
                    total_volume = total_volume + volume
                this.total_volume = total_volume
                this.total_weight = total_weight

    
    def _compute_periode_information(self):
        today = datetime.now().date()
        for this in self:
            periode_information = False
            if this.state in ['confirm', 'approve']:
                if today >= this.start_date and today <= this.end_date:
                    periode_information = 'running'
                elif today >= this.end_date:
                    periode_information = 'finished'
            this.periode_information = periode_information

    @api.depends('sale_order_ids', 'sale_order_ids.amount_total', 'sale_order_ids.state')
    def _compute_total_order(self):
        for this in self:
            total_all = 0.0
            query = """
                select sum(sol.price_total) as total_all
                from sale_order_line sol
                join sale_order so on sol.order_id = so.id
                join product_product pp on sol.product_id = pp.id
                join product_template pt on pp.product_tmpl_id = pt.id
                where so.sale_agreement_id = %s and so.state in ('sale', 'done') and
                    pt.type = 'product'
            """
            params = (this.id,)
            self.env.cr.execute(query, params)
            result = self.env.cr.dictfetchone()
            if result:
                total_all = result['total_all'] or 0.0
            this.total_order = total_all

    
    @api.depends('sale_order_ids')
    def _compute_orders_number(self):
        for agreement in self:
            agreement.order_count = len(agreement.sale_order_ids)

    @api.onchange('user_id')
    def _onchange_user_id(self):
        if not self.user_id:
            return
        values = {
            'currency_id': self.user_id.company_id.currency_id.id,
        }
        self.update(values)

    def fetch_sequence(self):
        self.ensure_one()
        if self.name == False or self.name == _('New'):
            self.name = self.env['ir.sequence'].next_by_code('sale.agreement')

    @api.model
    def create(self, vals):
        # <penambahan warning saat create dimana user tidak pilih pricelist
        price = vals.get('pricelist_id')
        if not price:
            raise UserError(_("No Pricelist Selected!"))
            # ====================================================>
        return super(SaleAgreement, self).create(vals)

    def ensure_product_in_pricelist(self):
        self.ensure_one()
        if not self.pricelist_id.id:
            raise ValidationError(_("No Pricelist Defined!"))
        
        product_in_pricelist = self.pricelist_id.item_ids.mapped('product_id') + self.pricelist_id.item_ids.mapped(lambda r:r.product_tmpl_id.product_variant_ids)
        not_in_pricelist = self.agreement_line_ids.mapped('product_id') - product_in_pricelist
        if len(not_in_pricelist):
            raise ValidationError(_("Some product not in pricelist. Please Check:\n\n%s") % ('\n'.join(not_in_pricelist.mapped('display_name'))))

    def btn_confirm(self):
        self.ensure_one()
        self.ensure_product_in_pricelist()
        if any(line.product_qty <= 0.0 for line in self.agreement_line_ids):
            deleted_product = []
            for line in self.agreement_line_ids.filtered(lambda r: r.product_qty == 0.0):
                deleted_product.append(line.product_id.name)
            joined_deleted_product ='</li><li>'.join(deleted_product)
            message = "All Products wich 0 qty will be deleted.<br/><ul><li>" + joined_deleted_product+'</ul>'
            form = self.env.ref('message_action_wizard.message_action_wizard_form_view')
            context = dict(self.env.context or {})
            context.update({
                'default_res_model_id':self.env['ir.model'].with_user(1).search([('model','=',self._name)]).id,
                'default_res_id':self.id,
                'default_messages':message,
                "default_action_confirm": "action_confirm"
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
            self.action_confirm()

    def _validate_agreement_lines(self):
        self.ensure_one()
        if not len(self.agreement_line_ids):
            raise UserError(_("No Product Selected on Agreement Lines!"))

    
    def action_confirm(self):
        self.ensure_one()
        if any(this.state != 'draft' for this in self):
            raise UserError(_('You just can confirm Draft Sale Agreement'))
        
        deleted_product = self.agreement_line_ids.filtered(lambda r: r.product_qty == 0.0)
        if deleted_product:
            deleted_product.unlink()
        
        self._validate_agreement_lines()
        # self.agreement_line_ids.constrains_float()
        self.fetch_sequence()
        return self.write({'state': 'confirm'})

    
    def action_approve(self):
        self.ensure_one()
        orders = self.filtered(lambda s: s.state == 'confirm')
        return orders.write({'state': 'approve'})

    
    def action_cancel(self):
        self.ensure_one()
        orders = self.filtered(lambda s: s.state in ['draft', 'confirm'])
        return orders.write({'state': 'cancel'})

    def action_locked(self):
        self.ensure_one()
        orders = self.filtered(lambda s: s.state in ['draft', 'confirm'])
        return orders.write({'state': 'locked'})
    
    def action_draft(self):
        orders = self.filtered(lambda s: s.state == 'cancel')
        return orders.write({'state': 'draft'})

    def action_done(self):
        orders = self.filtered(lambda s: s.state == 'approve')
        return orders.write({'state': 'done'})

    def create_so_from_sale_agreement(self):
        self.ensure_one()
        if fields.Date.today() > self.end_date:
            raise ValidationError(_('Sale Agreement already expired'))
        res = self.env['sale.order'].browse(self._context.get('id',[]))
        value = []
        pricelist = self.pricelist_id

        for data in self.agreement_line_ids:
            if pricelist:
                product_context = dict(self.env.context, partner_id=self.partner_id.id, date=fields.Date.today(), uom=data.product_uom.id)
                final_price, rule_id = pricelist.with_context(product_context).get_product_price_rule(data.product_id, data.product_qty, self.partner_id)
            
            else:
                final_price = data.product_id.standard_price
                
            value.append([0,0,{
                                'product_id' : data.product_id.id,
                                'name' : data.product_id.name,
                                'product_uom_qty' : 0,
                                'product_uom' : data.product_uom.id,
                                # 'date_planned' : str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                                'price_unit' : data.price_unit,
                                'tax_id':[(6,0,data.tax_ids.ids)],
                                }])
        partner_pricelist = self.env['partner.pricelist'].search([('partner_id','=',self.partner_id.id), ('team_id','=',self.team_id.id)])[0]
        sale_order = res.create({
                        'partner_id' : self.partner_id.id,
                        'date_order' : fields.Date.today(),
                        # 'order_line':value,
                        'payment_term_id': partner_pricelist.payment_term_id.id,
                        'sale_agreement_id': self.id,
                        'team_id':self.team_id.id,
                    })
        
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "views": [[False, "form"]],
            "res_id": sale_order.id,
        }

    def action_add_all_product(self):
        self.ensure_one()
        new_lines = []
        
        categ_ids = self.team_id.product_category_ids.ids
        
        division_price_list = self.env['partner.pricelist'].search([('team_id','=',self.team_id.id),('partner_id','=',self.partner_id.id)])

        partner_pricelist = division_price_list.pricelist_id
        product_ids = self.env['product.product'].with_context(pricelist=partner_pricelist.id).search([('categ_id','in',categ_ids)])
        
        
        for product in product_ids:
            # check if line with product exist
            # then refer to update
            
            # PRODUCTS EQUAL WITH LOOP
            
            line = self.agreement_line_ids.filtered(lambda r:r.product_id == product)
            if len(line):
                value = {
                    'product_uom' : product.uom_id.id,
                    'tax_ids':[(6,0,product.taxes_id.ids)],
                }
                line.update(value)
                # line.product_id_change()
                line._compute_discount()
            else:
                value = {
                    'agreement_id' : self.id,
                    'product_id' : product.id,
                    'product_uom' : product.uom_id.id,
                    'price_unit' : product.price,
                    'tax_ids':[(6,0,product.taxes_id.ids)],
                    'product_qty':0.0,
                }
                new_line = self.env['sale.agreement.line'].new(value)
                new_line.product_id_change()
                new_line._compute_discount()
                new_lines.append(new_line._convert_to_write({name: new_line[name] for name in new_line._cache}))
        
        if len(new_lines):
            line_id = self.env['sale.agreement.line'].create(new_lines)

        return {
            'effect': {
                'fadeout': 'fast',
                'message': _("All product setted!"),
                # 'img_url': '/sanqua_sale_flow/static/src/img/wow.png',
                'type': 'rainbow_man',
            }
        }


    def _get_sales_can_be_cancel(self):
        # multi possible
        sale_ids = self.env['sale.order']
        sales = self.mapped(lambda r:r.sale_order_ids.filtered(lambda r:r.state not in ['cancel']))

        if len(sales):
            # check picking
            for sale in sales:
                if all(sale.picking_ids.mapped(lambda r:r.state not in ['done','plant-confirmed','assigned'])):
                    sale_ids += sale
        
        return sale_ids
    
    def cancel_approved(self):
        self.ensure_one()
        sale_ids = self._get_sales_can_be_cancel()
        if sale_ids:
            form = self.env.ref('sale_agreement.sale_agreement_cancel_wizard_view_form')
            res = {
                'name': "%s - %s" % (_('Canceling Sale Order'), self.name),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.agreement.cancel.wizard',
                'view_id': form.id,
                'type': 'ir.actions.act_window',
                'context':{'default_agrement_id':self.id,'line_ids':sale_ids.ids},
                'target': 'new'
            }
            return res
        else:
            self.write({'state': 'cancel'})

class SaleAgreementLine(models.Model):
    _name = 'sale.agreement.line'
    _description = 'Sales Agreement Line'
    _order = 'agreement_id, id'

    @api.depends('agreement_id.sale_order_ids', 'agreement_id.sale_order_ids.state', 'product_qty')
    def _compute_qty_so(self):
        for line in self:
            qty_product_in_so = line.agreement_id.sale_order_ids.filtered(lambda so:so.state in\
                ('sale', 'done')).mapped('order_line').filtered(lambda x: x.product_id.id == line.product_id.id)
            tota_per_product = sum(so.product_uom_qty for so in qty_product_in_so)
            line.product_qty_sale_order = tota_per_product
            line.remaining_qty = line.product_qty - line.product_qty_sale_order

    agreement_id = fields.Many2one('sale.agreement', string='Agreement Reference',
        required=True, ondelete='cascade', index=True, copy=False)
    product_id = fields.Many2one('product.product', string='Product',
        change_default=True, ondelete='restrict', required=True)
    product_qty = fields.Float(string='Quantity', required=True,
        digits=dp.get_precision('Product Unit of Measure'), default=0.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure',
        domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    product_qty_sale_order = fields.Float(string='Quantity SO', store=True,
        digits=dp.get_precision('Product Unit of Measure'), compute='_compute_qty_so')
    price_unit = fields.Float('Unit Price', required=True, digits='Product Price', default=0.0)
    remaining_qty = fields.Float('Remain Qty', compute='_compute_qty_so', store=True, copy=False)

    disc_amount = fields.Float(string='Disc. Amount')
    discount = fields.Float(string='Discount (%)',compute='_compute_discount')
    discount_id = fields.Many2one('region.discount',string="Discount Region",compute='_compute_discount_region')
    tax_ids = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    price_tax = fields.Monetary(compute='_compute_price_subtotal', string='Price Tax',store=True)
    price_total = fields.Monetary(compute='_compute_price_subtotal', string='Price Total',store=True)
    price_subtotal = fields.Monetary(compute='_compute_price_subtotal', string='Price Subtotal',store=True)
    # price_subtotal2 = fields.Monetary(compute="_compute_price_subtotal", string="Price Subtotal After Tax")
    base_price = fields.Monetary(compute='_compute_price_subtotal', string='Base Price',store=True)
    currency_id = fields.Many2one(related='agreement_id.currency_id', string='Currency', readonly=True, track_visibility='onchange')
    
    @api.depends('product_qty', 'price_unit', 'tax_ids')
    def _compute_price_subtotal(self):
        for line in self:
            base_price = line.tax_ids.compute_all(
                price_unit=line.price_unit, currency=line.currency_id,
                quantity=line.product_qty, product=line.product_id,
                partner=line.agreement_id.partner_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in base_price.get('taxes', [])),
                'price_total': base_price['total_included'],
                'price_subtotal': base_price['total_excluded'],
                'base_price': base_price['total_excluded'],
            })

    @api.depends('disc_amount','price_unit','product_qty')
    def _compute_discount(self):
        for each in self:
            each.discount = 0.0
            each.price_unit = each.price_unit or 0.0
            each.disc_amount = each.disc_amount or 0.0
            if each.price_unit:
                each.discount = (each.disc_amount / (each.price_unit * each.product_qty)) * 100.0 if each.product_qty else 0.0
            else:
                each.discount = 0.0

    # @api.constrains('price_unit')
    # def constrains_float(self):
        
    #     if not self._context.get('force_constrains_float'):
    #         for rec in self:
    #             if rec.price_unit <= 0.0:
                    
    #                 price = formatLang(self.env, rec.price_unit, monetary=True, currency_obj=rec.agreement_id.currency_id)
    #                 raise UserError(_("Not a valid Price Unit on %s = %s") % (rec.product_id.display_name, rec.price_unit))

    @api.depends('product_id','agreement_id.team_id','agreement_id.partner_id.region_group_id')
    def _compute_discount_region(self):
        for rec in self:
            rec.discount_id = False
            
            region_discount = self.env['region.discount'].search([('team_id.id','=',rec.agreement_id.team_id.id),('region_group_id.id','=',self.agreement_id.partner_id.region_group_id.id)])
            rec.discount_id = region_discount.id


    def _get_display_price(self, product):
        if self.agreement_id.pricelist_id.discount_policy == 'with_discount':
            return product.with_context(pricelist=self.agreement_id.pricelist_id.id).price
        product_context = dict(self.env.context, partner_id=self.agreement_id.partner_id.id, date=fields.Date.today(), uom=self.product_uom.id)

        final_price, rule_id = self.agreement_id.pricelist_id.with_context(product_context).get_product_price_rule(self.product_id, self.product_uom_qty, self.agreement_id.partner_id)
        base_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id, self.product_uom_qty, self.product_uom, self.agreement_id.pricelist_id.id)
        if currency != self.agreement_id.pricelist_id.currency_id:
            base_price = currency._convert(
                base_price, self.order_id.pricelist_id.currency_id,
                self.agreement_id.company_id or self.env.company, fields.Date.today())
        return max(base_price, final_price)

    @api.onchange('product_id')
    def product_id_change(self):
        print("AGREE ID", self.agreement_id.pricelist_id.name)
        if not self.agreement_id.pricelist_id:
            raise UserError(_("No Pricelist Selected!"))
        if not self.product_id:
            return
        vals = {}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_qty'] = self.product_qty or 0.0
            vals['tax_ids'] = [(6,0,self.product_id.taxes_id.ids)]
        
        self.update(vals)
        for each in self:
            each.disc_amount = 0.0
            if each.agreement_id.region_group_id:
                get_disc = each.discount_id
                product_ids = get_disc.region_discount_product_ids.mapped('product_id.id')
                if each.product_id.id in product_ids:
                    for prod in get_disc.region_discount_product_ids:
                        if each.product_id.id == prod.product_id.id:
                            each.disc_amount = prod.disc_amount
        product = self.product_id.with_context(
            lang=self.agreement_id.partner_id.lang,
            partner=self.agreement_id.partner_id,
            quantity=vals.get('product_qty') or self.product_qty,
            date= fields.Date.today(),
            pricelist=self.agreement_id.pricelist_id.id,
            uom=self.product_uom.id
        )
        
        if self.agreement_id.pricelist_id and self.agreement_id.partner_id:
            vals['price_unit'] = self._get_display_price(product)
        self.update(vals)
        return
    
    @api.constrains('product_qty_sale_order', 'product_qty')
    def _check_maximum_qty_so_based_on_product_qty(self):
        """qty so <= product qty"""
        for order in self:
            #change to configurable
            if order.product_qty_sale_order > order.product_qty:
                raise ValidationError(_('Limit for product %s from %s is only %s but you plan to sell %s'
                                        %  (order.product_id.name, order.agreement_id.name, order.product_qty, order.product_qty_sale_order)))