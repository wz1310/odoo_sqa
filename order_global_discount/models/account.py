# -*- coding: utf-8 -*-
""" Customize Account Invoice """
from odoo import api, models, fields
from odoo.addons import decimal_precision as dp
import re
from odoo.tools.misc import formatLang, format_date, get_lang


class AccountMove(models.Model):
    _inherit = "account.move"
    
    global_discount = fields.Float(string="Global Dicount (%)")
    amount_global_discount = fields.Monetary(compute='_compute_amount_global_discount', 
        inverse="_inverse_amount_global_discount", string='Global Discount Amount', store=True)
    amount_untaxed_base = fields.Float('Amount untaxed base', compute='_compute_price_discount')

    @api.depends('line_ids.price_subtotal','line_ids.discount','line_ids.discount')
    def _compute_price_discount(self):
        for each in self:
            each.amount_untaxed_base = each.amount_untaxed_base or 0.0
            for line in each.line_ids:
                price_total = line.quantity * line.price_unit
                price_after_disc = price_total - (line.price_unit * line.discount / 100 * line.quantity)
                each.amount_untaxed_base += price_after_disc
                
    @api.depends('global_discount','amount_untaxed_base')
    def _compute_amount_global_discount(self):
        for inv in self:
            amount_untaxed = inv.amount_untaxed_base
            if amount_untaxed:
                inv.amount_global_discount = amount_untaxed * (inv.global_discount / 100)
            else:
                inv.global_discount = inv.global_discount or 0.0
                inv.amount_global_discount = inv.amount_global_discount or 0.0

    @api.depends('amount_global_discount','amount_untaxed_base')
    def _inverse_amount_global_discount(self):
        for inv in self:
            amount_untaxed = inv.amount_untaxed_base
            if amount_untaxed:
                inv.global_discount = (inv.amount_global_discount / amount_untaxed) * 100
            else:
                inv.global_discount = inv.global_discount or 0.0
                inv.amount_global_discount = inv.amount_global_discount or 0.0


    # @api.depends(
    #     'line_ids.debit',
    #     'line_ids.credit',
    #     'line_ids.currency_id',
    #     'line_ids.amount_currency',
    #     'line_ids.amount_residual',
    #     'line_ids.amount_residual_currency',
    #     'line_ids.payment_id.state','invoice_line_ids.price_subtotal', 'currency_id', 'company_id', 'type', 'global_discount', 'amount_global_discount')
    # def _compute_amount(self):
    #     invoice_ids = [move.id for move in self if move.id and move.is_invoice(include_receipts=True)]
    #     self.env['account.payment'].flush(['state'])
    #     if invoice_ids:
    #         self._cr.execute(
    #             '''
    #                 SELECT move.id
    #                 FROM account_move move
    #                 JOIN account_move_line line ON line.move_id = move.id
    #                 JOIN account_partial_reconcile part ON part.debit_move_id = line.id OR part.credit_move_id = line.id
    #                 JOIN account_move_line rec_line ON
    #                     (rec_line.id = part.debit_move_id AND line.id = part.credit_move_id)
    #                 JOIN account_payment payment ON payment.id = rec_line.payment_id
    #                 JOIN account_journal journal ON journal.id = rec_line.journal_id
    #                 WHERE payment.state IN ('posted', 'sent')
    #                 AND journal.post_at = 'bank_rec'
    #                 AND move.id IN %s
    #             UNION
    #                 SELECT move.id
    #                 FROM account_move move
    #                 JOIN account_move_line line ON line.move_id = move.id
    #                 JOIN account_partial_reconcile part ON part.debit_move_id = line.id OR part.credit_move_id = line.id
    #                 JOIN account_move_line rec_line ON
    #                     (rec_line.id = part.credit_move_id AND line.id = part.debit_move_id)
    #                 JOIN account_payment payment ON payment.id = rec_line.payment_id
    #                 JOIN account_journal journal ON journal.id = rec_line.journal_id
    #                 WHERE payment.state IN ('posted', 'sent')
    #                 AND journal.post_at = 'bank_rec'
    #                 AND move.id IN %s
    #             ''', [tuple(invoice_ids), tuple(invoice_ids)]
    #         )
    #         in_payment_set = set(res[0] for res in self._cr.fetchall())
    #     else:
    #         in_payment_set = {}

    #     for move in self:
    #         total_untaxed = 0.0
    #         total_untaxed_currency = 0.0
    #         total_tax = 0.0
    #         total_tax_currency = 0.0
    #         total_residual = 0.0
    #         total_residual_currency = 0.0
    #         total = 0.0
    #         total_currency = 0.0
    #         currencies = set()

    #         for line in move.line_ids:
    #             if line.currency_id:
    #                 currencies.add(line.currency_id)

    #             if move.is_invoice(include_receipts=True):
    #                 # === Invoices ===

    #                 if not line.exclude_from_invoice_tab:
    #                     # Untaxed amount.
    #                     total_untaxed += line.balance
    #                     total_untaxed_currency += line.amount_currency
    #                     total += line.balance
    #                     total_currency += line.amount_currency
    #                 elif line.tax_line_id:
    #                     # Tax amount.
    #                     total_tax += line.balance
    #                     total_tax_currency += line.amount_currency
    #                     total += line.balance
    #                     total_currency += line.amount_currency
    #                 elif line.account_id.user_type_id.type in ('receivable', 'payable'):
    #                     # Residual amount.
    #                     total_residual += line.amount_residual
    #                     total_residual_currency += line.amount_residual_currency
    #             else:
    #                 # === Miscellaneous journal entry ===
    #                 if line.debit:
    #                     total += line.balance
    #                     total_currency += line.amount_currency

    #         if move.type == 'entry' or move.is_outbound():
    #             sign = 1
    #         else:
    #             sign = -1
    #         move.amount_untaxed = sign * (total_untaxed_currency if len(currencies) == 1 else total_untaxed)
    #         move.amount_tax = sign * (total_tax_currency if len(currencies) == 1 else total_tax)
    #         move.amount_total = sign * (total_currency if len(currencies) == 1 else total)
    #         move.amount_residual = -sign * (total_residual_currency if len(currencies) == 1 else total_residual)
    #         move.amount_untaxed_signed = -total_untaxed
    #         move.amount_tax_signed = -total_tax
    #         move.amount_total_signed = abs(total) if move.type == 'entry' else -total
    #         move.amount_residual_signed = total_residual

    #         currency = len(currencies) == 1 and currencies.pop() or move.company_id.currency_id
    #         is_paid = currency and currency.is_zero(move.amount_residual) or not move.amount_residual

    #         # Compute 'invoice_payment_state'.
    #         if move.type == 'entry':
    #             move.invoice_payment_state = False
    #         elif move.state == 'posted' and is_paid:
    #             if move.id in in_payment_set:
    #                 move.invoice_payment_state = 'in_payment'
    #             else:
    #                 move.invoice_payment_state = 'paid'
    #         else:
    #             move.invoice_payment_state = 'not_paid'


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    amount_discount = fields.Monetary(string='Discount Amount', store=True)
    price_tax = fields.Float(string='Tax', store=True)

    # @api.depends('discount')
    # def _compute_amount_discount(self):
    #     for rec in self:
    #         rec.amount_discount = 0.0
            
    #     for line in self.filtered(lambda l: l.quantity and l.price_unit):
    #         line.amount_discount = 0.0
    #         if line.discount and line.quantity and line.price_unit:
    #             line.amount_discount = (line.discount / 100) * (line.quantity * line.price_unit)

    # def _inverse_amount_discount(self):
    #     for line in self.filtered(lambda l: l.quantity and l.price_unit):
    #         line.amount_discount = 0.0
    #         if line.discount and line.quantity and line.price_unit:
    #             line.discount = line.amount_discount / (line.quantity * line.price_unit) * 100

    # @api.depends('price_unit', 'multi_discounts', 'discount_fixed_line')
    # def _compute_display_discount(self):
    #     for line in self:
    #         discount = line.discount
    #         total_discount = line.discount

    #         if line.multi_discounts:
    #             discount_string_ids = re.findall(r"[-+]?\d*\.\d+|\d+", str(line.multi_discounts))
    #             total_discount = 0.0 if not discount_string_ids \
    #                 else line.compute_multi_discounts(discount_string_ids)
    #         if line.discount_fixed_line:
    #             if line.move_id.type in ['out_invoice', 'out_refund']:
    #                 price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
    #                 pr = (line.discount_fixed_line * line.quantity / (price_reduce * line.quantity)) * 100.0
    #             else:
    #                 price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
    #                 pr = (line.discount_fixed_line / (price_reduce * line.quantity)) * 100.0
    #             total_discount += pr
    #         line.update({
    #             'display_discount': total_discount,
    #             'discount': discount
    #         })

    
    # @api.model
    # def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes, move_type):
    #     ''' This method is used to compute 'price_total' & 'price_subtotal'.

    #     :param price_unit:  The current price unit.
    #     :param quantity:    The current quantity.
    #     :param discount:    The current discount.
    #     :param currency:    The line's currency.
    #     :param product:     The line's product.
    #     :param partner:     The line's partner.
    #     :param taxes:       The applied taxes.
    #     :param move_type:   The type of the move.
    #     :return:            A dictionary containing 'price_subtotal' & 'price_total'.
    #     '''
    #     res = {}

    #     # Compute 'price_subtotal'.
    #     price_unit_wo_discount = price_unit - discount
    #     subtotal = quantity * price_unit_wo_discount

    #     # Compute 'price_total'.
    #     if taxes:
    #         taxes_res = taxes._origin.compute_all(price_unit_wo_discount,
    #             quantity=quantity, currency=currency, product=product, partner=partner, is_refund=move_type in ('out_refund', 'in_refund'))
    #         res['price_subtotal'] = taxes_res['total_excluded']
    #         res['price_total'] = taxes_res['total_included']
    #     else:
    #         res['price_total'] = res['price_subtotal'] = subtotal
    #     #In case of multi currency, round before it's use for computing debit credit
    #     if currency:
    #         res = {k: currency.round(v) for k, v in res.items()}
    #     return res


    # def _get_price_total_and_subtotal(self, price_unit=None, quantity=None, discount=None, currency=None, product=None, partner=None, taxes=None, move_type=None):
    #     self.ensure_one()
    #     return self._get_price_total_and_subtotal_model(
    #         price_unit=price_unit or self.price_unit,
    #         quantity=quantity or self.quantity,
    #         discount=discount or self.discount_fixed_line,
    #         currency=currency or self.currency_id,
    #         product=product or self.product_id,
    #         partner=partner or self.partner_id,
    #         taxes=taxes or self.tax_ids,
    #         move_type=move_type or self.move_id.type,
    #     )
        