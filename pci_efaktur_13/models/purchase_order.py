
from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    tax_no = fields.Char(string='Tax Number', track_visibility='onchange')