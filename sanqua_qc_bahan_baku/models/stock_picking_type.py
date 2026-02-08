from odoo import api, fields, models, _

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    location_for_qc_bahan_baku = fields.Boolean('Used for QC Bahan Baku')
