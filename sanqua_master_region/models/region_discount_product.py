from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class RegionDiscountProduct(models.Model):
    _name = 'region.discount.product'
    _description = "Region Discount Product"

    region_discount_id = fields.Many2one('region.discount', string='Region',required=True)
    product_id = fields.Many2one('product.product', string='Product',required=True,ondelete='cascade',onupdate='cascade')
    currency_id = fields.Many2one('res.currency', string='Currency',required=True,default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one('res.company', related='region_discount_id.company_id',store=True)
    disc_amount = fields.Monetary(string='Disc. Amount', digits="Unit Price",required=True)
    team_id = fields.Many2one('crm.team', string='Division', compute="_compute_team_id", store=True, inverse=lambda self:True)

    allowed_product_category_ids = fields.Many2many(comodel_name="product.category", related='team_id.product_category_ids')

    @api.onchange('region_discount_id')
    def _onchange_region_discount_id(self):
        self.team_id = self.region_discount_id.team_id.id

    @api.onchange('team_id')
    def _onchange_team_id(self):
        allowed_product_category_ids = self.env['product.category']
        if self.team_id.id:
            allowed_product_category_ids = self.team_id.product_category_ids
        self.disc_amount = 0.0
        self.product_id = False
        self.allowed_product_category_ids = allowed_product_category_ids

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id.id:
            exist = self.region_discount_id.region_discount_product_ids.filtered(lambda r:r.product_id == self.product_id)
            
            if len(exist)>1:
                raise UserError(_("Product %s aready registered!") % (self.product_id.display_name))
        

    @api.depends('region_discount_id')
    def _compute_team_id(self):
        for rec in self:
            rec.team_id = rec.region_discount_id.team_id.id
    
    _sql_constraints = [('unique_product_on_same_region_team', 'unique(region_discount_id,product_id)', 'Product Must Unique in 1 Doc')]
    