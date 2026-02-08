from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

class SaleOrder(models.Model):
    """Inherit sale order"""
    _inherit = 'sale.order'

    note = fields.Text('Terms and conditions', track_visibility='onchange')
    partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address', track_visibility='onchange', readonly=True, required=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'sale': [('readonly', False)]}, help="Delivery address for current sales order.")
    product_category_ids = fields.Many2many('product.category', related="team_id.product_category_ids")

#Remove by ADI
    # @api.constrains('order_line')
    # def _check_max_item_order_line(self):
    #     """ max quotation is 20 item """
    #     for order in self:
    #         #change to configurable
    #         if len(order.order_line.filtered(lambda x : x.product_type != 'service')) > 20:
    #             raise ValidationError('Maximum items only 20')
    
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        print("onchange_partner_id")
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment terms
        - Invoice address
        - Delivery address
        """
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'fiscal_position_id': False,
            })
            return

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        partner_user = self.partner_id.user_id or self.partner_id.commercial_partner_id.user_id
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
        }
        print("VALUES",values)
        user_id = partner_user.id
        if not self.env.context.get('not_self_saleperson'):
            user_id = user_id or self.env.uid

        if self.env['ir.config_parameter'].sudo().get_param('account.use_invoice_terms') and self.env.company.invoice_terms:
            values['note'] = self.with_context(lang=self.partner_id.lang).env.company.invoice_terms
        self.update(values)
    
    @api.onchange('team_id')
    def onchange_team_id(self):
        """Create new onchange team_id"""
        if self.team_id and self.team_id.payment_term_id:
            self.payment_term_id = self.team_id.payment_term_id
