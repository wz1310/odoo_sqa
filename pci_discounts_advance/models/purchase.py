# -*- coding: utf-8 -*-

import logging
import re
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    """Custom on Purchase Order model"""
    _inherit = "purchase.order"

    @api.depends('order_line.price_total', 'order_line.total_discount_amount',
                 'order_line.base_price')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0
            total_discount_amount = 0.0
            base_price = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
                if line.total_discount_amount > 0:
                    total_discount_amount += line.total_discount_amount
                base_price += line.base_price
            order.update({
                'amount_untaxed': order.currency_id.round(amount_untaxed),
                'amount_tax': order.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
                'total_discount_amount': total_discount_amount,
                'base_price': base_price,
            })

    is_price_include = fields.Boolean(
        default=False,
        string='Tax Included in Price',
    )
    total_discount_amount = fields.Float(string='Total Discount', readonly=True,
        digits=dp.get_precision('Discount'), compute='_amount_all', store=True)
    base_price = fields.Float(digits=dp.get_precision('Base Price'),
        readonly=True, compute='_amount_all', store=True)


class PurchaseOrderLine(models.Model):
    """Custom on Purchase Order Line model"""
    _inherit = "purchase.order.line"

    multi_discounts = fields.Char(
        string='Discounts (%)', help='This field is used to allow multiple discounts, \
        How to used is: By adding multiple discount amounts seprated with by +. \
        If you apply 10+5+2 it will apply first 10(%) discount \
        and then it will apply 5(%) on new amount and then it will apply 2(%)',)
    discount = fields.Float(
        string='Discount (%)', digits=dp.get_precision('Discount'),
        default=0.0, compute='_compute_display_discount', store=True)
    display_discount = fields.Float(
        string='Total Discount (%)', digits=dp.get_precision('Discount'),
        compute='_compute_display_discount', default=0.0)
    discount_fixed_line = fields.Float(string='Discount (Rp)', digits=dp.get_precision('Discount_fixed'))
    total_discount_amount = fields.Float(string='Total Discount Amount', readonly=True,
        digits=dp.get_precision('Discount'), compute='_compute_amount', store=True)
    base_price = fields.Float(digits=dp.get_precision('Base Price'), readonly=True,
        compute='_compute_amount', store=True)

    @api.depends('multi_discounts', 'discount_fixed_line', 'price_unit', 'product_qty')
    def _compute_display_discount(self):
        for line in self:
            discount = line.discount or 0

            if line.multi_discounts:
                discount_string_ids = re.findall(r"[-+]?\d*\.\d+|\d+", str(line.multi_discounts))
                discount = 0.0 if not discount_string_ids \
                    else line.compute_multi_discounts(discount_string_ids)
            #price_reduce = line.price_unit * (1.0 - discount / 100.0)
            price_reduce = line.price_unit - line.amount_discount
            
            pr = 0
            if line.discount_fixed_line and line.price_unit:
                discount_fixed_line = line.discount_fixed_line * (1.0 - discount / 100.0)
                pr = (line.discount_fixed_line / (price_reduce * line.product_qty)) * 100
                discount += pr
            line.update({
                'display_discount': discount,
                'discount': discount
            })

    def compute_multi_discounts(self, discount_ids):
        """ This function is used to computation multi discounts, by regex string
        Allowing user to adding multiple discounts amount separated by + or / or, etc.
            * If you apply 10+5+2 it will apply first 10(%) discount
            * and then it will apply 5(%) on new amount and then it will apply 2(%)
        """
        price_unit = self.price_unit
        discounts = [float(disc) for disc in discount_ids]

        for disc in discounts:
            price_unit *= (1 - (disc or 0.0) / 100.0)

        discount_amount = 0.0 if self.price_unit == 0.0 \
            else (1 - price_unit / self.price_unit) * 100.0
        return discount_amount

    @api.depends('product_qty', 'price_unit', 'taxes_id', 'discount', 'discount_fixed_line')
    def _compute_amount(self):
        """Method to compute amount including discounts & taxes"""
        for line in self:
            vals = line._prepare_compute_all_values()
            taxes = line.taxes_id.compute_all(
                vals['price_unit'],
                vals['currency_id'],
                vals['product_qty'],
                vals['product'],
                vals['partner'])
            #discount = (line.discount/100)*line.price_unit
            discount = line.amount_discount
            total_discount_amount = line.taxes_id.compute_all(
                price_unit=discount, currency=line.order_id.currency_id,
                quantity=line.product_qty, product=line.product_id,
                partner=line.order_id.partner_id
            )
            base_price = line.taxes_id.compute_all(
                price_unit=line.price_unit, currency=line.order_id.currency_id,
                quantity=line.product_qty, product=line.product_id,
                partner=line.order_id.partner_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
                'base_price': base_price['total_excluded'],
                'total_discount_amount': total_discount_amount['total_excluded'],
            })

    def _prepare_compute_all_values(self):
        """replace base function"""
        # Hook method to returns the different argument values for the
        # compute_all method, due to the fact that discounts mechanism
        # is not implemented yet on the purchase orders.
        # This method should disappear as soon as this feature is
        # also introduced like in the sales module.
        self.ensure_one()
        #price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        price = self.price_unit - self.amount_discount
        return {
            'price_unit': price,
            'currency_id': self.order_id.currency_id,
            'product_qty': self.product_qty,
            'product': self.product_id,
            'partner': self.order_id.partner_id,
        }
    
    def _prepare_account_move_line(self, move):
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        res.update({
                    'multi_discounts': self.multi_discounts,
                    'discount_fixed_line': self.discount_fixed_line,
                    })
        return res