# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
import re

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    multi_discounts = fields.Char(
        string='Discounts (%)', help='This field is used to allow multiple discounts, How to used is: \
        By adding multiple discount amounts separated with by + / - or etc. \
        If you apply 10+5+2 it will apply first 10(%) discount \
        and then it will apply 5(%) on new amount and then it will apply 2(%)',
    )
    display_discount = fields.Float(
        string='Total Discount (%)', digits=dp.get_precision('Discount'),
        compute='_compute_display_discount',
        default=0.0
    )
    discount_fixed_line = fields.Float(string='Discount (Rp)')

    @api.depends('multi_discounts', 'discount_fixed_line')
    def _compute_display_discount(self):
        for line in self:
            line.update({
                'display_discount': line.discount,
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

    # @api.onchange('product_id', 'price_unit', 'product_uom', 'product_uom_qty',
    #               'tax_id', 'multi_discounts', 'discount_fixed_line')
    # def _onchange_discount(self):
    #     super(SaleOrderLine, self)._onchange_discount()

    #     discount = 0.0
    #     self.discount = 0
    #     if self.multi_discounts:
    #         discount_string_ids = re.findall(r"[-+]?\d*\.\d+|\d+",
    #             str(self.multi_discounts))
    #         if discount_string_ids:
    #             discount += self.compute_multi_discounts(discount_string_ids)

    #     pr = 0
    #     if self.discount_fixed_line and self.price_unit:
    #         pr = (self.discount_fixed_line * self.product_uom_qty / (self.price_reduce * self.product_uom_qty))*100
    #         discount += pr

    #     if not (self.product_id and self.product_uom and
    #             self.order_id.partner_id and self.order_id.pricelist_id and
    #             self.order_id.pricelist_id.discount_policy == 'without_discount' and
    #             self.env.user.has_group('sale.group_discount_per_so_line')):
    #         self.discount = discount
    #     else:
    #         self.discount += discount

    def _prepare_invoice_line(self):
        res = super(SaleOrderLine, self)._prepare_invoice_line()
        res.update({
            'multi_discounts': self.multi_discounts,
            'discount_fixed_line':self.discount_fixed_line
        })
        return res
