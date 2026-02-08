""" File pricelist discount"""
from odoo import api, fields, models, _
from datetime import datetime
from odoo.addons import decimal_precision as dp


class PricelistDiscount(models.Model):
    """ new object pricelist discount """
    _name = "pricelist.discount"
    _description = "Pricelist Discount"

    def _get_default_currency_id(self):
        return self.env.user.company_id.currency_id.id

    name = fields.Char('Pricelist Discount Name', required=True, translate=True)
    active = fields.Boolean('Active', default=True, help="If unchecked, it will allow you to hide the pricelist without removing it.")
    sequence = fields.Integer(default=16)
    compute_price = fields.Selection([
        ('fixed', 'Discount Amount'),
        ('percentage', 'Multi Discount Percentage'),
        ('other', 'Other Pricelist')], index=True, default='fixed')
    fixed_price = fields.Float('Discount (Rp)')
    percent_price = fields.Char('Discount Percentage')
    base_pricelist_discount_id = fields.Many2one('pricelist.discount', 'Other Pricelist Discount')
    other_compute_price = fields.Selection([
        ('fixed', 'Discount Amount'),
        ('percentage', 'Multi Discount Percentage')], index=True, default='')


    @api.onchange('compute_price')
    def _onchange_compute_price(self):
        if self.compute_price != 'fixed':
            self.fixed_price = 0.0
        if self.compute_price != 'percentage':
            self.percent_price = ''

    @api.onchange('other_compute_price')
    def _onchange_other_compute_price(self):
        if self.other_compute_price != 'fixed':
            self.fixed_price = 0.0
        if self.other_compute_price != 'percentage':
            self.percent_price = ''

    def name_get(self):
        return [(pricelist_disc.id, '%s' % (pricelist_disc.name)) for pricelist_disc in self]
