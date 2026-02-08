""" Stock Picking """
from odoo import models, fields, _ , api

class StockPicking(models.Model):
    """ Inherit stock.picking"""
    _inherit = "stock.picking"

    mrp_pbbh_id = fields.Many2one('mrp.pbbh',string="PBBH", track_visibility='onchange')
    #shift_id = fields.Many2one('mrp.shift','Shift Muat')
    
    # def button_validate(self):
    #     res = super(StockPicking, self).button_validate()
    #     pbbh = self.env['mrp.pbbh'].search([
    #         ('name','=',self.origin)
    #     ])
    #     pbbh.write({
    #         'state' : 'done'
    #     })
    #     return res

    # @api.onchange('mrp_pbbh_id')
    # def _onchange_mrp_pbbh_id(self):
    #     if self.mrp_pbbh_id:
    #         location = self.env['stock.location'].search([
    #             ('company_id','=',self.company_id.id),
    #             ('usage','=','transit')
    #         ],limit=1)
    #         for rec in self:
    #             pbbh_line = []
    #             for line in rec.mrp_pbbh_id.mrp_pbbh_line_ids:
    #                 vals = (0, 0, {
    #                     'product_id' : line.product_id.id,
    #                     'product_uom' : line.product_id.uom_id.id,
    #                     'product_uom_qty' : line.qty
    #                 })
    #                 pbbh_line.append(vals)
    #             rec.update({'move_ids_without_package': pbbh_line,
    #                         'location_dest_id':location.id if location else False})
