# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

class StockLocation(models.Model):
    """ inherit stock.location"""
    _inherit = "stock.location"

    check_for_transit_bahan_baku = fields.Boolean(
        string='Transit Penerimaan Bahan Baku',
        default=False)

    production_for_pbbh = fields.Boolean('Production Location for PBBH')