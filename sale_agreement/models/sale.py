"""File Sale Order"""
from datetime import datetime, timedelta

from lxml import etree

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as dtf

import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    """class inherit sale.order"""
    _inherit = 'sale.order'

    sale_agreement_id = fields.Many2one('sale.agreement', copy=False,
        string='Agreement Reference')
    product_ids = fields.Many2many('product.product',
        string='Agreement Lines', compute='_compute_product_ids', store=True)

    @api.depends('sale_agreement_id', 'sale_agreement_id.product_ids', 'team_id')
    def _compute_product_ids(self):
        for data in self:
            domain = []
            if data.sale_agreement_id:
                domain = [(6, 0, data.sale_agreement_id.product_ids.ids)]
            else:
                if data.team_id and data.team_id.product_category_ids:
                    product_ids = self.env['product.product'].search([('categ_id', 'in', data.team_id.product_category_ids.ids)])
                    domain = [(6, 0, product_ids.ids)]
            data.product_ids = domain


    def _check_agreement_qty(self):
        for this in self:
            if this.sale_agreement_id:
                for line in this.order_line.filtered(lambda r:r.product_id.type!='service' and r.order_id.is_substitute_order==False):
                    product_sales_agreement = this.sale_agreement_id.agreement_line_ids.filtered(lambda p: p.product_id.id == line.product_id.id)
                    total_product_qty = line.product_qty
                    if not line.is_reward_line and line.product_uom_qty > product_sales_agreement.remaining_qty:
                        raise UserError(_('Remaining qty for product %s from %s is only %s but you plan to sell %s'
                                          % (product_sales_agreement.product_id.name, this.sale_agreement_id.name, product_sales_agreement.remaining_qty, line.product_qty)))

    def action_confirm(self):
        self._check_agreement_qty()
        return super(SaleOrder, self).action_confirm()

    @api.onchange('sale_agreement_id')
    def _onchange_sale_agreement_id(self):
        if not self.sale_agreement_id:
            return
        agreement = self.sale_agreement_id
        if not self.origin or agreement.name not in agreement.origin.split(', '):
            if self.origin:
                if agreement.name:
                    self.origin = self.origin + ', ' + agreement.name
            else:
                self.origin = agreement.name
        self.user_id = False
        if agreement.partner_id:
            self.partner_id = agreement.partner_id.id
        # if agreement.pricelist_id:
        #     self.pricelist_id = agreement.pricelist_id.id
        self.onchange_partner_id()
        date_order = fields.Datetime.now()
        if date_order.date() > agreement.end_date:
            date_order = datetime(
                    year=agreement.end_date.year, 
                    month=agreement.end_date.month,
                    day=agreement.end_date.day,
                ) + timedelta(hours=2)
        elif date_order.date() < agreement.start_date:
            date_order = datetime(
                    year=agreement.start_date.year, 
                    month=agreement.start_date.month,
                    day=agreement.start_date.day,
                ) + timedelta(hours=2)
        self.date_order = date_order
        self.user_id = agreement.user_id.id
        self.company_id = agreement.company_id.id
        self.currency_id = agreement.currency_id.id
        # Create SO lines if necessary
        # order_lines = []
        # for line in agreement.agreement_line_ids:
        #     # Compute taxes
        #     # Create SO line
        #     line_values = {
        #         'name': line.product_id.display_name,
        #         'product_id': line.product_id.id,
        #         'product_uom': line.product_id.uom_po_id.id,
        #         'product_uom_qty': 0,
        #         'price_unit': line.price_unit,
        #         # 'date_planned': date_order,
        #     }
            
        #     order_lines.append((0, 0, line_values))
        # self.order_line = order_lines

    @api.onchange('partner_id', 'team_id')
    def onchange_partner_team_id(self):
        if not self.partner_id or not self.team_id:
            self.update({'partner_pricelist_id': False})
            return
        vals = {}
        if self.sale_agreement_id:
            vals['pricelist_id'] = self.sale_agreement_id.pricelist_id.id
        elif self.partner_id.partner_pricelist_ids:
            pp = self.partner_id.partner_pricelist_ids.filtered(
                lambda l: l.team_id.id == self.team_id.id)
            if pp:
                pp = pp[0]
                vals = {'partner_pricelist_id':pp.id}
                if pp.pricelist_id:
                    vals['pricelist_id'] = pp.pricelist_id.id
                self.update(vals)
        return

class SaleOrderLine(models.Model):
    """class inherit sale.order.line"""
    _inherit = 'sale.order.line'


    agreement_id = fields.Many2one('sale.agreement', related="order_id.sale_agreement_id", readonly=True)
    agreement_line_id = fields.Many2one('sale.agreement.line', string="Agreement Line", compute='_compute_agreement_id', store=True, copy=False)


    @api.depends('product_id','order_id')
    def _compute_agreement_id(self):
        for rec in self:
            # rec.agreement_id = rec.order_id.sale_agreement_id.id
            res = False
            if rec.is_reward_line==False:
                res = rec.order_id.sale_agreement_id.agreement_line_ids.filtered(lambda r:r.product_id.id == rec.product_id.id).id
            rec.agreement_line_id = res
    # @api.constrains('product_id')
    # def _constrains_product_id(self):
    #     for rec in self.filtered(lambda r: r.order_id.agreement_id.id):
    #         rec.agreement_line_id = r.order_id.agreement_id.agreement_line_ids.filtered(lambda r:r.product_id.id == rec.product_id.id).id

    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        if self.order_id.sale_agreement_id:
            agreement_price = self._check_price_product(self.product_id, self.order_id.sale_agreement_id)
            if len(agreement_price):
                self.price_unit = agreement_price.product_qty
        return res
    
    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        res = super(SaleOrderLine, self).product_uom_change()
        if self.order_id.sale_agreement_id:
            agreement_price = self._check_price_product(self.product_id, self.order_id.sale_agreement_id)
            
            if len(agreement_price):
                self.update({'discount_fixed_line':agreement_price.disc_amount, "tax_id":[(6, 0, agreement_price.tax_ids.ids)]})
        return res


    @api.returns('sale.agreement.line',lambda value:value.id if value.id else False)
    def _check_price_product(self, product, sale_agreement):
        return sale_agreement.agreement_line_ids.filtered(lambda x: x.product_id.id == product.id)