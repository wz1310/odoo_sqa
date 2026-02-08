# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class StockMove(models.Model):
    _inherit = 'stock.move'
    display_name = fields.Char(string="Disp. Name", compute="_compute_display_name")

    def _compute_display_name(self):
        # print(self._context)
        # # print('>>>>>>>>>>>>>>>>>>>>>>>>>')
        
        super()._compute_display_name()
        for rec in self.sudo():
            name = "%s | %s" % (rec.product_id.display_name, rec.product_uom_qty, )
            rec.display_name += name

    def name_get(self):
        res = []
        if not self._context.get('is_substitute'):
            return super().name_get()

        for rec in self:
            name = "%s | %s" % (rec.product_id.display_name, rec.product_uom_qty, )
            res += [(rec.id, name)]
        return res