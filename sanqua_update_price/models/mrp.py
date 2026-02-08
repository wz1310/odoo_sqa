"""File MRP"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    """class inherit mrp.production"""
    _inherit = 'mrp.production'

    def _get_qc_finish_move_value(self, product_id, product_uom_qty, product_uom,
                                  picking_type_id, location_id, location_dest_id):
        return {
            'product_id': product_id,
            'product_uom_qty': product_uom_qty,
            'product_uom': product_uom,
            'name': self.name,
            'date': fields.Date.today(),
            'date_expected': self.date_planned_finished,
            'picking_type_id': picking_type_id,
            'location_id': location_id.id,
            'location_dest_id': location_dest_id.id,
            'company_id': self.company_id.id,
            'qc_production_id': self.id,
            'warehouse_id': location_dest_id.get_warehouse().id,
            'origin': self.name,
            'group_id': self.procurement_group_id.id,
            'propagate_cancel': self.propagate_cancel,
            'propagate_date': self.propagate_date,
            'propagate_date_minimum_delta': self.propagate_date_minimum_delta,
            'price_unit': self.produksi_amount / self.product_qty,
        }

    #update price for stock move that related with mo
    def update_price_in_stock_move_for_mo(self):
        move_ids_ids = self.env['stock.move'].search([('qc_production_id', '!=', False)])
        for data in move_ids_ids:
            if data.qc_production_id:
                data.price_unit = data.qc_production_id.produksi_amount / data.qc_production_id.product_qty
