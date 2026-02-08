# -*- coding: utf-8 -*-
""" Customize Purchase Order """
from datetime import timedelta
import pytz
import re
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class PurchaseOrder(models.Model):
    """ Inherit purchase order """

    _inherit = "purchase.order"

    global_discount = fields.Float(string="Global Dicount (%)")
    amount_global_discount = fields.Monetary(compute='_compute_amount_global_discount', 
        inverse="_inverse_amount_global_discount", string='Global Discount Amount', store=True)
    amount_untaxed_base = fields.Float('Amount untaxed base', compute='_compute_price_discount')

    @api.depends('order_line.price_subtotal','order_line.discount','order_line.discount_percent_line')
    def _compute_price_discount(self):
        for each in self:
            each.amount_untaxed_base = each.amount_untaxed_base or 0.0
            for line in each.order_line:
                price_total = line.product_qty * line.price_unit
                price_after_disc = price_total - (line.price_unit - line.amount_discount) * line.product_qty
                each.amount_untaxed_base += price_after_disc



    @api.depends('global_discount','amount_untaxed_base')
    def _compute_amount_global_discount(self):
        for order in self:
            amount_untaxed = order.amount_untaxed_base
            if amount_untaxed:
                order.amount_global_discount = amount_untaxed * (order.global_discount / 100)
            else:
                order.global_discount = order.global_discount or 0.0
                order.amount_global_discount = order.amount_global_discount or 0.0

    @api.depends('amount_global_discount','amount_untaxed_base')
    def _inverse_amount_global_discount(self):
        for order in self:
            amount_untaxed = order.amount_untaxed_base
            if amount_untaxed:
                order.global_discount = (order.amount_global_discount / amount_untaxed) * 100
            else:
                order.global_discount = order.global_discount or 0.0
                order.amount_global_discount = order.amount_global_discount or 0.0


    @api.depends('order_line.price_total', 'global_discount', 'amount_global_discount')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0
            total_discount_amount = 0.0
            base_price = 0.0
            for line in order.order_line:
                if line.total_discount_amount > 0:
                    total_discount_amount += line.total_discount_amount
                base_price += line.base_price
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            # amount_untaxed -= order.amount_global_discount
            order.update({
                'amount_untaxed': order.currency_id.round(amount_untaxed),
                'amount_tax': order.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
                'total_discount_amount': total_discount_amount,
                'base_price': base_price,
            })

    def action_view_invoice(self):
        res = super(PurchaseOrder, self).action_view_invoice()
        res['context']['default_global_discount'] = self.global_discount
        res['context']['default_amount_global_discount'] = self.amount_global_discount
        return res


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"


    amount_discount = fields.Monetary(compute='_compute_amount_discount', inverse='_inverse_amount_discount', string='Discount Amount / QTY', store=True)
    multi_discounts = fields.Char(
        string='Discounts (%)', help='This field is used to allow multiple discounts, \
        How to used is: By adding multiple discount amounts seprated with by +. \
        If you apply 10+5+2 it will apply first 10(%) discount \
        and then it will apply 5(%) on new amount and then it will apply 2(%)',compute='_compute_multi_disc')
    discount_percent_line = fields.Float(string="Discount(%)",store=True)
    propotional_percent = fields.Float(string="Disc Global", compute='_compute_global_discount',inverse='')
    amount_propotional = fields.Float(string="Amount Disc Global", compute='_compute_global_discount')
    discount = fields.Float(
        string='Discount (%)', digits=dp.get_precision('Discount'),
        default=0.0, compute='_compute_display_discount', store=True)
    display_discount = fields.Float(
        string='Total Discount (%)', digits=dp.get_precision('Discount'),
        compute='_compute_display_discount', default=0.0)

    @api.depends('multi_discounts', 'discount_fixed_line', 'price_unit', 'product_qty', 'discount_percent_line')
    def _compute_display_discount(self):
        for line in self:
            discount = line.discount_percent_line or 0
            if line.multi_discounts:
                discount_string_ids = re.findall(r"[-+]?\d*\.\d+|\d+", str(line.multi_discounts))
                discount = 0.0 if not discount_string_ids \
                    else line.compute_multi_discounts(discount_string_ids)
            price_reduce = line.price_unit * (1.0 - discount / 100.0)
            pr = 0
            if line.discount_fixed_line and line.price_unit:
                discount_fixed_line = line.discount_fixed_line * (1.0 - discount / 100.0)
                pr = (line.discount_fixed_line / (price_reduce * line.product_qty)) * 100
                discount += pr
            line.update({
                'display_discount': discount,
                'discount': discount
            })

    @api.depends('order_id.amount_global_discount','order_id.global_discount')
    def _compute_global_discount(self):
        for line in self.filtered(lambda l: l.product_qty and l.price_unit):
            price_subtotal = line.price_subtotal or 1
            base_price = line.order_id.amount_untaxed_base or 1
            line.propotional_percent = price_subtotal / base_price * 100
            line.amount_propotional = line.order_id.amount_global_discount * (line.propotional_percent / 100)


    @api.depends('discount_percent_line','price_unit')
    def _compute_amount_discount(self):
        for rec in self:
            rec.amount_discount = 0.0
        for line in self.filtered(lambda l: l.product_qty and l.price_unit):
            if line.discount_percent_line and line.product_qty and line.price_unit:
                #line.amount_discount = (line.discount_percent_line / 100) * (line.product_qty * line.price_unit)
                #Change to unit price
                line.amount_discount = (line.discount_percent_line / 100) * (line.price_unit)

    @api.depends('amount_discount')
    def _inverse_amount_discount(self):
        for line in self.filtered(lambda l: l.product_qty and l.price_unit):
            if line.product_qty and line.price_unit:
                #line.discount_percent_line = (line.amount_discount / (line.product_qty * line.price_unit)) * 100
                #Change to unit price
                line.discount_percent_line = (line.amount_discount / (line.price_unit)) * 100

    def _prepare_compute_all_values(self):
        vals = super(PurchaseOrderLine, self)._prepare_compute_all_values()
        price = self.price_unit - self.amount_discount
        vals['price_unit'] = price
        #vals['price_unit'] = (1 - (self.discount / 100)) * self.price_unit
        return vals

    @api.depends('product_qty', 'price_unit', 'taxes_id', 'discount', 'amount_discount')
    def _compute_amount(self):
        return super(PurchaseOrderLine, self)._compute_amount()

    def _prepare_account_move_line(self, move):
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        res.update({
            'discount' : self.display_discount,
            'amount_discount': self.amount_discount,
            'price_tax': self.price_tax,
        })
        return res

    @api.depends('discount_percent_line','order_id.global_discount')
    def _compute_multi_disc(self):
        for each in self:
            global_disc = str(each.order_id.global_discount)
            disc_percent_line = str(each.discount_percent_line)
            multi_disc = ""
            if (each.order_id.global_discount):
                multi_disc = global_disc
            if (each.discount_percent_line):
                multi_disc = disc_percent_line
            if (each.discount_percent_line and each.order_id.global_discount):
                multi_disc = disc_percent_line + '+' + global_disc
            each.multi_discounts = multi_disc

    # @api.depends('product_qty', 'price_unit', 'taxes_id', 'discount', 'discount_fixed_line')
    # def _compute_amount(self):
    #     """Method to compute amount including discounts & taxes"""
    #     for line in self:
    #         vals = line._prepare_compute_all_values()
    #         taxes = line.taxes_id.compute_all(
    #             vals['price_unit'],
    #             vals['currency_id'],
    #             vals['product_qty'],
    #             vals['product'],
    #             vals['partner'])
    #         discount = (line.discount/100)*line.price_unit #discount per item
    #         discount_global = (line.price_unit * line.product_qty) * (line.order_id.global_discount/100)
    #         print(discount)
    #         print(discount_global)
    #         total_discount_amount = line.taxes_id.compute_all(
    #             price_unit=discount, currency=line.order_id.currency_id,
    #             quantity=line.product_qty, product=line.product_id,
    #             partner=line.order_id.partner_id
    #         )
    #         base_price = line.taxes_id.compute_all(
    #             price_unit=line.price_unit, currency=line.order_id.currency_id,
    #             quantity=line.product_qty, product=line.product_id,
    #             partner=line.order_id.partner_id)
    #         line.update({
    #             'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
    #             'price_total': taxes['total_included'],
    #             'price_subtotal': taxes['total_excluded'],
    #             'base_price': base_price['total_excluded'],
    #             'total_discount_amount': total_discount_amount['total_excluded'],
    #         })