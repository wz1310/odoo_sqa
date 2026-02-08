# -*- encoding: utf-8 -*-
from odoo import fields, models, api, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    promotion_ids = fields.One2many('sale.order.promotion','sale_id', string="Promotion Lines")
    is_promotion =  fields.Boolean(string="Is promotion",default=False)
    order_promotion_id = fields.Many2one('sale.order.promotion',string="Sale Order Promotion")


    # PCI Version
    # Disable at: 28/12/2021
    # Description: It makes the discount deduct twice
    # @api.constrains('write_date','state','amount_total')

    # MIS@SanQua version
    # Created at: 28/12/2021
    # Description: It make the discount deduct once
    @api.constrains('state')
    def _constrains_state(self):
        print('>>> call _constrains_state(): /sale_promotion/models/sale_order.py')
        for rec in self.filtered(lambda r:r.is_promotion==False):
            # print('>>> rec : ' + str(rec))
            # print('>>> rec.write_date : ' + str(rec.write_date))
            # print('>>> rec.state : ' + str(rec.state))
            # print('>>> rec.amount_total : ' + str(rec.amount_total))
            if rec.state not in ['sale','done']:
                rec.recompute_coupon_lines(confirm_all=True)
                for line in rec.order_line:
                    line._compute_amount()