# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

class MisApvStockLocation(models.Model):
    """ inherit stock.location"""
    _inherit = "stock.location"

    apv_for_matrix = fields.Boolean()

    # @api.model
    # def _get_custom_domain_warehouse_id(self):
    #     print('>>> Self.company_id : ' + str(self.company_id.id))
    #     return [('company_id', '=', self.company_id.id)]
    # warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse',
    #                                domain=lambda self: self._get_custom_domain_warehouse_id())

    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
