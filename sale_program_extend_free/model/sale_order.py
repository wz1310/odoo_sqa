# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.constrains('write_date','state','amount_total')
    def _constrains_state(self):
        print('>>> call _constrains_state(): /sale_program_extend_free/model/sale_order.py')
        for rec in self:
            if rec.state not in ['sale','done']:
                rec.recompute_coupon_lines(confirm_all=True)
                for line in rec.order_line:
                    line._compute_amount()             

    def _get_reward_values_product(self, program):
        print("_get_reward_values_product")
        if program.free_product_selection in ['same_on_line','custom'] \
            and program.free_product_method == 'extended' \
            and program.reward_type=='product':
            return self._get_reward_values_product_extended(program)
        else:
            return super()._get_reward_values_product(program)

    def _get_reward_values_discount(self, program):
        print("_get_reward_values_discount")
        if program.discount_type == 'fixed_amount' and program.fix_amount_method == 'amount_per_unit':
            return self._get_reward_values_discount_extended(program)
        else:
            return super()._get_reward_values_discount(program) 
        
    def _get_reward_values_discount_extended(self,program):
        print("_get_reward_values_discount_extended")
        order_lines = self.order_line.filtered(lambda line: line.product_id) - self._get_reward_lines()
        products = order_lines.mapped('product_id')
        vals = []
        discount_product_lines = self.order_line.filtered(lambda r: r.product_id in program._get_valid_products(products))
        for rec in discount_product_lines:
            data = {
                    'name': _("Discount: ") + program.name,
                    'product_id': program.discount_line_product_id.id,
                    'price_unit': - (rec.product_uom_qty * self._get_reward_values_discount_fixed_amount(program)),
                    'product_uom_qty': 1.0,
                    'product_uom': program.discount_line_product_id.uom_id.id,
                    'is_reward_line': True,
                    'tax_id': [(4, tax.id, False) for tax in program.discount_line_product_id.taxes_id],
                }
            vals.append(data)
        return vals

    def _get_reward_values_product_extended(self, program):
        order_lines = self.order_line.filtered(lambda line: line.product_id) - self._get_reward_lines()
        products = order_lines.mapped('product_id')
        vals = []
        order_lines = self.order_line.filtered(lambda r: r.product_id in program._get_valid_products(products))
        vals = []
        for rec in order_lines:
            if rec.product_uom_qty >= program.rule_min_quantity:
                if program.free_product_selection=='custom':
                    product = program.reward_product_id
                    product_uom = product.uom_id
                else:
                    product = rec.product_id
                    product_uom = rec.product_uom
                
                data =  {
                        'product_id': product.id,
                        'price_unit': 0.0,
                        'product_uom_qty': int(rec.product_uom_qty / program.rule_min_quantity) * program.reward_product_quantity,
                        'is_reward_line': True,
                        'name': _("Free Product") + " - " + product.name,
                        'product_uom': product_uom.id,
                        'tax_id': False,
                        'program_promo_id' : program.id if rec.program_promo_id == False else rec.program_promo_id,
                        'create_date_promo' : rec.create_date if rec.create_date_promo == False else rec.create_date_promo,
                        'start_date_promo' : program.rule_date_from if rec.start_date_promo == False else rec.start_date_promo,
                        'end_date_promo' : program.rule_date_to if rec.end_date_promo == False else rec.end_date_promo,
                    }
                vals.append(data)
        return vals

    def _get_reward_line_values(self, program):
        self.ensure_one()
        self = self.with_context(lang=self.partner_id.lang)
        program = program.with_context(lang=self.partner_id.lang)
        if program.reward_type == 'discount':
            return self._get_reward_values_discount(program)
        elif program.reward_type == 'product':
            reward_values = self._get_reward_values_product(program)
            if isinstance(reward_values,list):
                return reward_values
            else:
                return [self._get_reward_values_product(program)]

    def _update_existing_reward_lines(self):
        '''Update values for already applied rewards'''
        def update_line(order, lines, values):
            '''Update the lines and return them if they should be deleted'''
            lines_to_remove = self.env['sale.order.line']
            # Check commit 6bb42904a03 for next if/else
            # Remove reward line if price or qty equal to 0
            if values['product_uom_qty'] and values['price_unit']:
                lines.write(values)
            else:
                if program.reward_type != 'free_shipping':
                    # Can't remove the lines directly as we might be in a recordset loop
                    lines_to_remove += lines
                else:
                    values.update(price_unit=0.0)
                    lines.write(values)
            return lines_to_remove

        self.ensure_one()
        order = self
        applied_programs = order._get_applied_programs_with_rewards_on_current_order()
        for program in applied_programs:
            values = order._get_reward_line_values(program)
            lines = order.order_line.filtered(lambda line: line.product_id == program.discount_line_product_id)
            if program.reward_type == 'discount' and program.discount_type == 'percentage':
                lines_to_remove = lines
                # Values is what discount lines should really be, lines is what we got in the SO at the moment
                # 1. If values & lines match, we should update the line (or delete it if no qty or price?)
                # 2. If the value is not in the lines, we should add it
                # 3. if the lines contains a tax not in value, we should remove it
                for value in values:
                    value_found = False
                    for line in lines:
                        # Case 1.
                        if not len(set(line.tax_id.mapped('id')).symmetric_difference(set([v[1] for v in value['tax_id']]))):
                            value_found = True
                            # Working on Case 3.
                            lines_to_remove -= line
                            lines_to_remove += update_line(order, line, value)
                            continue
                    # Case 2.
                    if not value_found:
                        order.write({'order_line': [(0, False, value)]})
                # Case 3.
                lines_to_remove.unlink()
            else:
                for value in values:
                    update_line(order, lines, value).unlink()