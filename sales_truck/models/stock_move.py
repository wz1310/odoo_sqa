from odoo import api, fields, models, _

class StockMove(models.Model):
    _inherit = "stock.move"

    dispenser_lot_id = fields.Many2one('stock.production.lot', string='Lot/Serial Number', track_visibility='onchange')
    available_to_invoice = fields.Boolean(string='Available To Invoice',default=True)