from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ResBranch(models.Model):
    _inherit = 'res.branch'

    related_company_id = fields.Many2one('res.company', string="Company")
    sequence_id = fields.Many2one('ir.sequence', string="Sequence")