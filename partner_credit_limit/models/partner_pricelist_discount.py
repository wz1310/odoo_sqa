""" File partner pricelist"""
from odoo import api, fields, models, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class PartnerPricelistDiscount(models.Model):
    """ new object partner pricelist discount"""
    _name = "partner.pricelist.discount"
    _description = "Partner Pricelist Discount"

    partner_id = fields.Many2one('res.partner', 'Partner',
        ondelete='cascade', index=True, required=True)
    sequence = fields.Integer(default=16)
    active = fields.Boolean('Active', default=True, help="If unchecked, it will allow you to hide the pricelist without removing it.")
    categ_id = fields.Many2one('product.category', 'Category Product', index=True, required=True)
    pricelist_discount_id = fields.Many2one('pricelist.discount')
    discount_percent = fields.Char('Discount %')
    discount_amount = fields.Float('Discount (Rp)')
    total_discount_percent = fields.Char('Total Discount %', compute="_compute_pricelist_discount_id")
    total_discount_amount = fields.Float('Total Discount Value', compute="_compute_pricelist_discount_id")

    @api.depends('pricelist_discount_id', 'pricelist_discount_id.compute_price', 'discount_percent', 'discount_amount')
    def _compute_pricelist_discount_id(self):
        for rec in self:
            rec.total_discount_amount = 0.0
            rec.total_discount_percent = 0
            if rec.pricelist_discount_id:
                discount_amount = 0
                discount_percent = ''
                if rec.pricelist_discount_id.compute_price == 'fixed':
                    discount_amount = rec.pricelist_discount_id.fixed_price

                elif rec.pricelist_discount_id.compute_price == 'percentage':
                    discount_percent = rec.pricelist_discount_id.percent_price

                elif rec.pricelist_discount_id.base_pricelist_discount_id.compute_price:
                    if rec.pricelist_discount_id.base_pricelist_discount_id.compute_price == 'fixed':
                        if rec.pricelist_discount_id.other_compute_price == 'fixed':
                            discount_amount = rec.pricelist_discount_id.base_pricelist_discount_id.fixed_price + rec.pricelist_discount_id.fixed_price
                        else:
                            discount_amount = rec.pricelist_discount_id.base_pricelist_discount_id.fixed_price
                            discount_percent = rec.pricelist_discount_id.percent_price
                    elif rec.pricelist_discount_id.base_pricelist_discount_id.compute_price == 'percentage':
                        if rec.pricelist_discount_id.other_compute_price == 'percentage':
                            discount_percent = rec.pricelist_discount_id.base_pricelist_discount_id.percent_price + '+' + rec.pricelist_discount_id.percent_price
                        else:
                            discount_amount = rec.pricelist_discount_id.fixed_price
                            discount_percent = rec.pricelist_discount_id.base_pricelist_discount_id.percent_price
                rec.total_discount_amount =  rec.discount_amount + discount_amount
                if discount_percent and not rec.discount_percent:
                    rec.total_discount_percent = discount_percent
                elif not discount_percent and rec.discount_percent:
                    rec.total_discount_percent = rec.discount_percent
                elif discount_percent and rec.discount_percent:
                    rec.total_discount_percent = discount_percent + '+' + self.discount_percent
            else:
                discount_amount = rec.discount_amount
                discount_percent = rec.discount_percent
                rec.total_discount_amount = discount_amount
                rec.total_discount_percent = discount_percent
