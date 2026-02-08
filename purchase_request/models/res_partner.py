from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = "res.partner"
    

    customer = fields.Boolean(string='Customer',default=False)
    supplier = fields.Boolean(string='Supplier',default=False)