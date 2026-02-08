# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MisInherInvAdj(models.Model):
    _inherit = 'stock.inventory'

    aac_id = fields.Many2one('account.analytic.account', string="Analytic account id")

    def _action_done(self):
        res = super(MisInherInvAdj,self)._action_done()
        sm_filter = ""
        sm_id = self.line_ids.inventory_id.move_ids.ids
        if self.aac_id:
            if len(sm_id) == 1:
                data_tuple = "(%s)" % sm_id[0]
            else:
                data_tuple = tuple(sm_id)
            sm_filter = ("WHERE stock_move_id IN %s") % (str(data_tuple))
            query = """
            UPDATE account_move_line SET analytic_account_id = %s
            WHERE move_id in (SELECT id FROM account_move """+sm_filter+""")
            """
            self._cr.execute(query, (self.line_ids.inventory_id.aac_id.id,))
        return res