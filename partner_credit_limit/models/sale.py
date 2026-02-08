"""File Sale """
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    """class inherit sale.order"""
    _inherit = 'sale.order'

    partner_pricelist_id = fields.Many2one('partner.pricelist',
        string='Partner Pricelist')


    @api.onchange('partner_id', 'team_id')
    def onchange_partner_team_id(self):
        print("onchange_partner_team_id")
        if not self.partner_id or not self.team_id:
            self.update({'partner_pricelist_id': False,})
            return
        if self.partner_id.partner_pricelist_ids:
            pp = self.partner_id.partner_pricelist_ids.filtered(
                lambda l: l.team_id.id == self.team_id.id)
            if pp:
                pp = pp[0]
                vals = {'partner_pricelist_id':pp.id}
                if pp.pricelist_id:
                    vals['pricelist_id'] = pp.pricelist_id.id
                self.update(vals)
            return

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        if 'partner_id' in vals and 'team_id' in vals:
            res.sudo().onchange_partner_team_id()
        return res

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        if 'partner_id' in vals or 'team_id' in vals:
            for this in self:
                this.sudo().onchange_partner_team_id()
        return res


class SaleOrderLine(models.Model):
    """class inherit sale.order.line"""
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        multi_discounts = ''
        discount_fixed_line = 0
        if self.order_id and self.order_id.partner_id and self.order_id.team_id:
            if self.product_id.categ_id:
                multi_discounts = self.product_id.categ_id.percent_discount
                discount_fixed_line = self.product_id.categ_id.fixed_discount
            pp_discount = self.order_id.partner_id.partner_pricelist_discount_ids.filtered(
                lambda l: l.categ_id.id == self.product_id.categ_id.id)
            if not pp_discount:
                pp_discount = self.order_id.partner_id.partner_pricelist_discount_ids.filtered(
                lambda l: l.categ_id.id == self.product_id.categ_id.parent_id.id)
            if pp_discount:
                pp_discount = pp_discount[0]
                if multi_discounts and pp_discount.total_discount_percent:
                    multi_discounts = multi_discounts + '+' + pp_discount.total_discount_percent
                elif multi_discounts:
                    multi_discounts = multi_discounts
                elif not multi_discounts and pp_discount.total_discount_percent:
                    multi_discounts = pp_discount.total_discount_percent
                else:
                    multi_discounts =  pp_discount.total_discount_percent
                discount_fixed_line = discount_fixed_line + pp_discount.total_discount_amount
            self.update({
                'multi_discounts':multi_discounts,
                'discount_fixed_line':discount_fixed_line
            })
        return res
