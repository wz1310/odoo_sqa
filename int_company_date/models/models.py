
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
import datetime
from datetime import date
_logger = logging.getLogger(__name__)

class InterCompanyPricelist(models.Model):
    _name = "inter.company.pricelist"
    _description = "Inter Company Pricelist"
    _inherit = ['mail.thread', 'mail.activity.mixin']


    company_id = fields.Many2one('res.company', required=True, default=lambda self:self.env.company.id)


    partner_company_id = fields.Many2one('res.company', required=True)
    partner_id = fields.Many2one('res.partner', related="partner_company_id.partner_id", readonly=True)

    pricelist_id = fields.Many2one('product.pricelist', required=True)


    @api.model
    def get_product_fixed_price(self,company,partner,product):
        date_now = date.today()
        print("DATE NOW",date_now)
        pricelist = self.get_intercompany_pricelist(company, partner)
        if len(pricelist):
            p_pricelist = pricelist.pricelist_id.item_ids.filtered(lambda r:r.product_id.id==product.id and r.date_start<=date_now and r.date_end>=date_now)
            print("Price list", p_pricelist)
            if len(p_pricelist)==1:
                return p_pricelist.fixed_price
            elif len(p_pricelist)==0:
                raise UserError(_("Pricelist for product %s not defined on Inter Company Pricelist %s - %s") % (product.display_name, pricelist.company_id.display_name, pricelist.partner_company_id.display_name,))
            else:
                p_pricelist = p_pricelist.sorted('id', reverse=True)
                return p_pricelist[0].fixed_price
        raise UserError(_("Please make sure pricelist method via Product Variant!"))

    @api.model
    def get_intercompany_pricelist(self, company, partner):
        return self.sudo().search([('company_id','=',company.id),('partner_id','=',partner.id)])