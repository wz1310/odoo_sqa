from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    # qty_produced = fields.Float(compute="_get_produced_qty", string="Quantity Produced",store=True)
    # produktivitas_mesin = fields.Float(compute="_get_productivitas_machine", string="Produktivitas Mesin",store=True)

    # @api.depends('workorder_ids.state', 'move_finished_ids', 'move_finished_ids.quantity_done', 'is_locked')
    # def _get_produced_qty(self):
    #     for production in self:
    #         done_moves = production.move_finished_ids.filtered(lambda x: x.state != 'cancel' and x.product_id.id == production.product_id.id)
    #         qty_produced = sum(done_moves.mapped('quantity_done'))
    #         production.qty_produced = qty_produced
    #     return True


    # @api.depends('state', 'move_finished_ids', 'move_finished_ids.quantity_done', 'kapasitas')
    # def _get_productivitas_machine(self):
    #     for production in self:
    #         produktivitas_mesin = 0.0
    #         if production.move_finished_ids:
    #             if production.qty_produced and production.kapasitas:
    #                 produktivitas_mesin = production.qty_produced / production.kapasitas * 100
    #         production.produktivitas_mesin = produktivitas_mesin
