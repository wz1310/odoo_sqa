# coding: utf-8
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)



class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    is_asset = fields.Boolean("Is an Asset")
    non_asset_type = fields.Selection([("saleable", "Saleable Product"), ("operational", "Operational"), ("material", "Material"),('promotion','Promotion')], "Non Asset Type")
    product_classification = fields.Selection([('bahanbaku','Bahan Baku'),
                                               ('barangsetengahjadi','Barang 1/2 Jadi'),
                                               ('barangjadi','Barang Jadi'),
                                               ('sparepart','Sparepart'),
                                               ('bahankimia','Bahan Kimia'),
                                               ('lainlain','Lain-Lain')],'Product Classification')



    @api.constrains('non_asset_type')
    def constrains_non_asset_type(self):
        for rec in self:
            if rec.is_asset == False and rec.non_asset_type==False:
                raise UserError(_("Non Asset Type must be selected when product defined as non asset!"))

    @api.onchange('is_asset')
    def _onchange_is_asset(self):
        if self.is_asset==True:
            self.type = 'product'

    @api.constrains('is_asset')
    def constrains_asset(self):
        for rec in self:
            if rec.is_asset==True:
                if rec.type not in ['product']:
                    raise UserError(_("If this product as an asset so must require to storeable the product"))
                rec.non_asset_type = False #make sure always false if is_asset = True


class ProductProduct(models.Model):
    _inherit = 'product.product'
    is_asset = fields.Boolean(string="Is an Asset", related="product_tmpl_id.is_asset")
    non_asset_type = fields.Selection(related="product_tmpl_id.non_asset_type")
    product_classification = fields.Selection(related="product_tmpl_id.product_classification")
