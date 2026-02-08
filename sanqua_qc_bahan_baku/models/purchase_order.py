from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.purchase.models.purchase import PurchaseOrder as Purchase

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # @api.onchange('order_line')
    # def onchange_order_line(self):
    #     for data in self:
    #         bahan_baku = False
    #         route_bahan_baku_qc_id = self.env.ref('sanqua_qc_bahan_baku.route_wh_qc')
    #         for line in data.order_line:
    #             if any(route.id == route_bahan_baku_qc_id.id for route in line.product_id.route_ids):
    #                 bahan_baku = True
    #         if bahan_baku:
    #             picking_type_qc_bahan_baku_id = self.env['stock.picking.type'].search([('location_for_qc_bahan_baku', '=', True),('company_id','=',self.env.company.id)], limit=1)
    #             if not picking_type_qc_bahan_baku_id:
    #                 raise UserError(_('Please set location for qc bahan baku'))
    #             data.picking_type_id = picking_type_qc_bahan_baku_id
    #         else:
    #             data.picking_type_id = self._get_picking_type(self.env.context.get('company_id') or self.env.company.id)
