from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockLocation(models.Model):
    _inherit = 'stock.location'

    other_wh_can_read = fields.Boolean(string="Other Plant can Read?", default=False)