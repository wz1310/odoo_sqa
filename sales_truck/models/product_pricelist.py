from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    def _read(self, fields):
        return super(ProductPricelist, self.sudo())._read(fields)

class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    def _read(self, fields):
        return super(ProductPricelistItem, self.sudo())._read(fields)