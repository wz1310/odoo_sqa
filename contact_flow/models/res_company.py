from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = "res.company"
    
    auto_delete_oustand_approval = fields.Integer(string="Waiting approval will delete in", default=4)
    