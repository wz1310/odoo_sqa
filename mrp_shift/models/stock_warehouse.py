""" Stock Warehouse """
from odoo import models, fields, _ , api

class StockWarehouse(models.Model):
    """ Inherit stock.warehouse"""
    _inherit = "stock.warehouse"

    location_raw_material_id = fields.Many2one('stock.location', check_company=True)
    location_raw_material_id_2 = fields.Many2one('stock.location', check_company=True)
    raw_material_type_id = fields.Many2one('stock.picking.type', string="Raw Material Operation Type", check_company=True)
    production_type_id = fields.Many2one('stock.picking.type', string='Production Operation Type', check_company=True)
