from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    hide_zero_price = fields.Boolean(string='Hide zero price', store=True)

class AccountMove(models.Model):
    _inherit = 'account.move'

    summary_invoice_line_ids = fields.One2many('summary.invoice.line','move_id', track_visibility='onchange', compute='_compute_invoice_line_ids',store=True, readonly=False)
    # include_tax = fields.Boolean(string='Tax', store=True, default=lambda self: self.env.company.id != 2)
    include_tax = fields.Boolean(string='Tax', store=True, default=True)
    hide_zero_price = fields.Boolean(string='Hide zero price', store=True)
    summary_invoice_amount_untaxed = fields.Float(string='Untaxed Amount', store=True)
    summary_invoice_amount_tax = fields.Float(string='Tax', store=True)
    summary_invoice_amount_total = fields.Float(string='Total', store=True)

    # @api.depends('include_tax')
    # def _set_default_value(self):
    #     for rec in self:
    #         print('>>> Di sini...')
    #         if self.env.company.id == 2 :
    #             rec.include_tax = False
    #         else:
    #             rec.include_tax = True

    @api.depends('invoice_line_ids')
    def _compute_invoice_line_ids(self):
        for rec in self:
            rec.summary_invoice_line_ids = False
            # print('>>> Here')
            # print('>>> invoice_line_ids : ' + str(rec.invoice_line_ids))
            #  test 123

            if len(rec.invoice_line_ids) > 0 :
                index = 1
                amount_untaxed = 0
                amount_tax = 0
                amount_total = 0
                prod_promo = []
                cek_promo = False
                for product in rec.invoice_line_ids.mapped('product_id'):
                    for x in rec.invoice_line_ids:
                        if 'Free Product' in x.name:
                            # print("FREE")
                            prod_promo.append(x.product_id.id)
                    if product.id in prod_promo:
                        cek_promo = True
                    else:
                        cek_promo = False
                    # print('>>> index : ' + str(index))
                    qty = sum([x.quantity * -1 if x.move_id.type in ['in_refund', 'out_refund']
                               else x.quantity for x in rec.invoice_line_ids.filtered(
                        lambda r: r.product_id.id == product.id)])

                    # Check the ppn
                    taxes = rec.invoice_line_ids.filtered(lambda r: r.product_id.id == product.id)
                    is_price_include = False
                    prev_tax = False
                    for rec_tax in taxes:
                        tax = False
                        tax = rec_tax.tax_ids.ids

                        # print('----------------------------------------------------')
                        # print('>>> Product Name: ' + str(product.name))
                        # print('>>> tax: ' + str(tax))
                        # print('----------------------------------------------------')

                        if tax:
                            # print('>>> Yes Tax')
                            account_tax = self.env['account.tax'].search([('id', '=', tax)])
                            #
                            # print('----------------------------------------------------')
                            # print('>>> Product Name: ' + str(product.name))
                            # print('>>> price_include: ' + str(account_tax.price_include))
                            # print('----------------------------------------------------')
                            #
                            # print('>>> Company ID 1: ' + str(self.env.company.id))
                            # print('>>> Company ID 2: ' + str(self.env.user.company_id.id))
                            if self.env.company.id == 2:
                                # print("COMPANY",self.env.company.id)
                                if account_tax.price_include:
                                    is_price_include = True
                                else:
                                    if is_price_include:
                                        tax = prev_tax
                                prev_tax = tax
                            else:
                                if not account_tax.price_include:
                                    is_price_include = False
                                else:
                                    if prev_tax:
                                        tax = prev_tax
                                prev_tax = tax

                        else:
                            tax = prev_tax

                    subtoal = 0

                    # for x in rec.invoice_line_ids.filtered(lambda r: r.product_id.id == product.id):
                    #     print('----------------------------------------------------')
                    #     print('>>> Product Name: ' + str(product.name))
                    #     print('>>> Price unit : ' + str(x.price_unit))
                    #     print('>>> Quantity : ' + str(x.quantity))

                    if is_price_include:
                        subtoal = sum([((x.price_unit - x.discount - x.discount_fixed_line) * x.quantity) * -1 if x.move_id.type in ['in_refund', 'out_refund']
                                       else ((x.price_unit - x.discount - x.discount_fixed_line) * x.quantity) for x in rec.invoice_line_ids.filtered(
                            lambda r: r.product_id.id == product.id)])
                        # print("subtoal",subtoal)

                        price_subtotal = sum([((x.price_unit - x.discount - x.discount_fixed_line) * x.quantity) * -1 if x.move_id.type in ['in_refund', 'out_refund']
                                              else ((x.price_unit - x.discount - x.discount_fixed_line) * x.quantity) for x in rec.invoice_line_ids.filtered(
                            lambda r: r.product_id.id == product.id)])
                    else:
                        subtoal = sum([x.price_subtotal * -1 if x.move_id.type in ['in_refund', 'out_refund']
                                       else x.price_subtotal for x in rec.invoice_line_ids.filtered(
                            lambda r: r.product_id.id == product.id)])
                        price_subtotal = sum(
                            [x.price_subtotal * -1 if x.move_id.type in ['in_refund', 'out_refund']
                             else x.price_subtotal for x in rec.invoice_line_ids.filtered(
                                lambda r: r.product_id.id == product.id)])

                    # if is_price_include:
                    #     dpp = 100/110
                    #     print("is_price_include",is_price_include)
                    #     subtoal = sum([((x.price_unit) * x.quantity) * -1  if x.move_id.type in ['in_refund', 'out_refund']
                    #                    else ((x.price_unit) * x.quantity) for x in rec.invoice_line_ids.filtered(
                    #         lambda r: r.product_id.id == product.id)])
                    #     # print("subtoal",subtoal)
                    #     price_subtotal = sum([((x.price_unit * x.quantity)-(x.discount_fixed_line*x.quantity)) * -1 *dpp if x.move_id.type in ['in_refund', 'out_refund']
                    #                           else ((x.price_unit * x.quantity)-x.discount_fixed_line*x.quantity) *dpp for x in rec.invoice_line_ids.filtered(
                    #         lambda r: r.product_id.id == product.id)])
                    # else:
                    #     print("NOT is_price_include",is_price_include)
                    #     subtoal = sum([x.price_subtotal * -1 if x.move_id.type in ['in_refund', 'out_refund']
                    #                    else x.price_subtotal for x in rec.invoice_line_ids.filtered(
                    #         lambda r: r.product_id.id == product.id)])
                    #     price_subtotal = sum(
                    #         [x.price_subtotal * -1 if x.move_id.type in ['in_refund', 'out_refund']
                    #          else x.price_subtotal for x in rec.invoice_line_ids.filtered(
                    # #             lambda r: r.product_id.id == product.id)])

                    # print('>>> is_price_include: ' + str(is_price_include))
                    # print('----------------------------------------------------')

                    # subtoal = sum([x.price_subtotal * -1 if x.move_id.type in ['in_refund', 'out_refund']
                    #                else x.price_subtotal for x in rec.invoice_line_ids.filtered(
                    #     lambda r: r.product_id.id == product.id)])

                    # if is_price_include:
                    #     discount = sum([x.discount * -1 if x.move_id.type in ['in_refund', 'out_refund']
                    #                             else x.discount for x in rec.invoice_line_ids.filtered(
                    #         lambda r: r.product_id.id == product.id)])
                    #     discount_fixed_line = sum([x.discount_fixed_line * -1 if x.move_id.type in ['in_refund', 'out_refund']
                    #                     else x.discount_fixed_line for x in rec.invoice_line_ids.filtered(
                    #         lambda r: r.product_id.id == product.id)])

                    if is_price_include:
                        discount = sum([x.discount * -1 if x.move_id.type in ['in_refund', 'out_refund']
                                                else x.discount for x in rec.invoice_line_ids.filtered(
                            lambda r: r.product_id.id == product.id)])
                        discount_fixed_line = sum([x.discount_fixed_line * x.quantity if x.move_id.type in ['in_refund', 'out_refund']
                                        else x.discount_fixed_line * x.quantity for x in rec.invoice_line_ids.filtered(
                            lambda r: r.product_id.id == product.id)])
                    else:
                        # print("IS PRICE",is_price_include)
                        # print("ELSE??????????")
                        discount = 0
                        discount_fixed_line = 0
                    # if cek_promo == True:
                    #     # print("PROMO",prod_promo)
                    #     discount_fixed_line = (discount_fixed_line*0)+sum([x.discount_fixed_line * -1 if x.move_id.type in ['in_refund', 'out_refund']
                    #         else x.discount_fixed_line *x.quantity for x in rec.invoice_line_ids.filtered(
                    #             lambda r: r.product_id.id == product.id)])/qty
                    #     # print("discount_fixed_line",discount_fixed_line)
                    # else:
                    #     # print("NO PROMO",prod_promo)
                    #     subtoal = subtoal + sum([(x.discount + x.discount_fixed_line)*x.quantity for x in rec.invoice_line_ids.filtered(
                    #         lambda r: r.product_id.id == product.id)])
                    #     # print("subtoal",subtoal)
                    #     fin_sub = subtoal-x.price_subtotal
                    #     price_subtotal = subtoal- fin_sub
                    if qty > 0:
                        if tax:

                            amount_tax = amount_tax + ( price_subtotal * (account_tax.amount / 100 ) )
                            # print("tax")
                            data = {
                                'product_id': product.id,
                                'name': product.name,
                                'account_id': rec.invoice_line_ids.filtered(lambda r: r.product_id.id == product.id)[0].account_id.id,
                                'analytic_account_id': rec.invoice_line_ids.filtered(lambda r: r.product_id.id == product.id)[0].analytic_account_id.id,
                                'quantity': qty,
                                'product_uom_id': rec.invoice_line_ids.filtered(lambda r: r.product_id.id == product.id)[0].product_uom_id.id,
                                'price_unit': subtoal/qty if qty > 0 else 0,
                                'discount': discount,
                                'discount_fixed_line': discount_fixed_line/qty,
                                # 'tax_ids': [(6, 0, rec.invoice_line_ids.filtered(lambda r: r.product_id.id == product.id)[0].tax_ids.ids)],
                                'tax_ids': [(6,0,tax)],
                                'price_subtotal': price_subtotal/1.1,

                            }
                        else:
                            # print("no tax")
                            data = {
                                'product_id': product.id,
                                'name': product.name,
                                'account_id': rec.invoice_line_ids.filtered(lambda r: r.product_id.id == product.id)[
                                    0].account_id.id,
                                'analytic_account_id':
                                    rec.invoice_line_ids.filtered(lambda r: r.product_id.id == product.id)[
                                        0].analytic_account_id.id,
                                'quantity': qty,
                                'product_uom_id':
                                    rec.invoice_line_ids.filtered(lambda r: r.product_id.id == product.id)[
                                        0].product_uom_id.id,
                                'price_unit': subtoal / qty if qty > 0 else 0,
                                'discount': discount,
                                'discount_fixed_line': discount_fixed_line,
                                # 'tax_ids': [(6, 0, rec.invoice_line_ids.filtered(lambda r: r.product_id.id == product.id)[0].tax_ids.ids)],
                                # 'tax_ids': [(6, 0, tax)],
                                'price_subtotal': price_subtotal,

                            }

                        amount_untaxed = amount_untaxed + data['price_subtotal']
                        rec.summary_invoice_line_ids = [(0, 0, data)]
                        # amount_untaxed = amount_untaxed + price_subtotal
                        # rec.summary_invoice_line_ids = [(0, 0, data)]
                    index += 1
                    # if is_price_include:
                    #     amount_tax = 0
                # rec.summary_invoice_amount_untaxed = amount_untaxed
                # rec.summary_invoice_amount_tax = amount_tax
                # rec.summary_invoice_amount_total = amount_untaxed + amount_tax
                rec.summary_invoice_amount_untaxed = amount_untaxed
                rec.summary_invoice_amount_tax = amount_tax/1.1
                rec.summary_invoice_amount_total = rec.summary_invoice_amount_untaxed + rec.summary_invoice_amount_tax

    @api.onchange('hide_zero_price')
    def do_hide_zero_price(self):
        for rec in self:
            ini = rec.hide_zero_price
            if len(rec.summary_invoice_line_ids) > 1:
                for line in rec.summary_invoice_line_ids:
                    if line.price_unit <= 0:
                        # raise UserError(_(line._origin.id))
                        move_line = self.env['summary.invoice.line'].search(
                            [('id', '=', line._origin.id)])
                        move_line.hide_zero_price = ini


    def btn_clear_tax(self):
        # account_move_line_ids = self.env['account.move.line'].search([('move_id','=',self.id)])
        # for move_line in account_move_line_ids:
        #     if not move_line.exclude_from_invoice_tab:
        #         move_line.tax_ids = [(3, move_line.id)]
        # self._recompute_dynamic_lines(True,True)
        for rec in self.invoice_line_ids:
            print('>>> Here (' + str(rec.id) + ') ...:' + str(rec.tax_ids))
            for tax in rec.tax_ids:
                if rec.tax_ids:
                    rec.tax_ids = [(3, tax.id, False)]
                    # rec.write({'tax_ids': [(3, tax.id, False)]})
                    # rec._recompute_debit_credit_from_amount_currency()
                    # rec._onchange_mark_recompute_taxes()
                    # self._recompute_tax_lines(recompute_tax_base_amount=True)
                    # self._recompute_dynamic_lines(recompute_tax_base_amount=True)

        # for rec in self.invoice_line_ids:
        #     for tax in rec.tax_ids:
        #         if rec.tax_ids:
        #             # deduct_val = rec.price_subtotal
        #             for line in rec.tax_ids.invoice_repartition_line_ids:
        #                 if line.repartition_type == 'tax':





        # self._recompute_tax_lines()
        # self._recompute_dynamic_lines(True, True)
        # for rec in self.invoice_line_ids:
        #     print('>>>')

    # def write(self,vals):
    #     res = super(AccountMove, self).write(vals)
    #     for x in self.summary_invoice_line_ids:
    #         x.sudo().write({'discount_fixed_line': 25})
    #     return res